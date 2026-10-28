"""
M03 - Điều phối câu hỏi, bằng chứng và câu trả lời của Verified Sales Agent.

Luồng chính:
    CommentEvent / QueueItem -> memory -> phân giải SKU và intent
    -> KnowledgeEngine -> provider tạo candidate -> AnswerVerifier
    -> cập nhật memory -> AgentResponse.

Mặc định module dùng lexical retrieval và provider xác định, không gọi LLM
qua mạng. Các quy tắc nhận diện intent dựa trên từ khóa và có phạm vi hạn chế;
đây chưa phải bộ phân loại tổng quát hay cơ chế chống prompt injection hoàn chỉnh.
"""
from dataclasses import replace
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import yaml

from hostra_ai.core.schemas import AgentResponse, CommentEvent
from .answer_verifier import AnswerVerifier, CandidateAnswer
from .conversation_memory import ConversationMemory
from .comment_queue import QueueItem
from .knowledge.models import EvidencePackage


# ============================================================
# 1. PROVIDER - TẠO CÂU TRẢ LỜI ỨNG VIÊN
# ============================================================

class LLMProvider(Protocol):
    """
    Giao diện nội bộ để thay provider tạo candidate.

    Provider nhận câu hỏi, SKU, intent và evidence; kết quả vẫn phải qua
    AnswerVerifier. Protocol này không tự tạo kết nối hay gọi API OpenAI.
    """
    def generate(self, query: str, resolved_sku_ids: tuple[str, ...],
                 intent: str, evidence: EvidencePackage) -> CandidateAnswer: ...


class DeterministicProvider:
    """
    Tạo candidate offline từ catalog và một số trích đoạn FAQ được hỗ trợ.

    Các con số giá, tồn kho và thông số lấy từ catalog trong EvidencePackage.
    Những trích đoạn FAQ chỉ được dùng khi hit tương ứng được truy xuất và
    không mang cờ needs_review. Candidate chưa phải câu trả lời đã xác minh.
    """
    def generate(self, query: str, resolved_sku_ids: tuple[str, ...],
                 intent: str, evidence: EvidencePackage, *, context=None) -> CandidateAnswer:
        """Dựng các mệnh đề và refs tương ứng; báo lỗi khi thiếu fact/FAQ cần dùng."""
        products = {item.sku_id: item.value for item in evidence.catalog_evidence if item.field_path is None}
        clauses = []
        for sku in resolved_sku_ids:
            p = products[sku]
            name = p['brand']
            specs = p['specifications']
            if intent in ('price_inquiry', 'comparison', 'price_discrepancy'):
                price = f"{p['price_vnd']:,}".replace(',', '.')
                clauses.append(f"Giá {name} trong phiên demo HOSTRA là {price} đồng")
            elif intent == 'stock_inquiry':
                clauses.append(f"{name}: {p['stock_quantity']} máy trong phiên demo HOSTRA")
            elif intent in ('upgrade_inquiry', 'advisory'):
                if intent == 'advisory' and 'chỉnh ảnh' in query.casefold() and specs['display'].get('panel'):
                    clauses.append(f"{name} có màn hình {specs['display']['panel']}, tần số quét {specs['display']['refresh_rate_hz']}Hz")
                for field, label in (('ram', 'RAM'), ('storage', 'SSD')):
                    q = query.casefold()
                    if intent == 'upgrade_inquiry' and any(term in q for term in ('ram', 'ssd', 'ổ cứng')):
                        if field == 'ram' and 'ram' not in q:
                            continue
                        if field == 'storage' and 'ssd' not in q and 'ổ cứng' not in q:
                            continue
                    val = specs[field]['upgradable']
                    state = 'chưa xác nhận khả năng nâng cấp' if val is None else 'có thể nâng cấp' if val else 'không thể nâng cấp'
                    clauses.append(f'Về {name}, {label} {state}')
            elif intent == 'spec_inquiry':
                q = query.casefold()
                if 'pin' in q:
                    clauses.append(f"{name} có pin {specs['battery_wh']}Wh")
                elif 'ram' in q:
                    clauses.append(f"{name} có RAM {specs['ram']['capacity_gb']}GB")
                elif 'ssd' in q:
                    clauses.append(f"{name} có SSD {specs['storage']['capacity_label']}")
                elif 'cpu' in q or 'chip' in q:
                    clauses.append(f"{name} có CPU {specs['cpu']['model']}")
                elif specs['display'].get('panel'):
                    display = specs['display']
                    clauses.append(f"{name} có màn hình {display['panel']}, tần số quét {display['refresh_rate_hz']}Hz")
                else:
                    clauses.append(f'{name}: chưa xác nhận tấm nền màn hình')
            else:
                raise ValueError('Unsupported intent')
        # Tính chênh lệch từ giá catalog hiện tại, không cố định số tiền trong code.
        if intent == 'comparison' and len(resolved_sku_ids) == 2:
            cheaper, dearer = sorted((products[s] for s in resolved_sku_ids), key=lambda p: p['price_vnd'])
            diff = f"{dearer['price_vnd'] - cheaper['price_vnd']:,}".replace(',', '.')
            clauses.append(f"{cheaper['brand']} rẻ hơn {dearer['brand']} {diff} đồng trong phiên demo HOSTRA")
        refs = [f'catalog:{sku}' for sku in resolved_sku_ids]
        # Phần tư vấn hiện dùng một số FAQ ID và trích đoạn cụ thể, không phải
        # tóm tắt tự do mọi FAQ được retriever trả về.
        if intent in ('advisory', 'price_discrepancy'):
            wanted = ('FAQ-SALES-005',) if intent == 'price_discrepancy' else (('FAQ-COMPARE-008',) if 'chỉnh ảnh' in query.casefold() else ('FAQ-COMPARE-005',))
            hit = next((h for h in evidence.faq_hits if h.metadata.get('faq_id') in wanted and h.metadata.get('needs_review') is False), None)
            if hit is None:
                raise ValueError('Relevant reviewed FAQ not retrieved')
            answer = hit.retrieval_text.splitlines()[-1].replace('**', '').strip('“”')
            sentences = re.split(r'(?<!\d)\.\s+', answer)
            if intent == 'price_discrepancy':
                excerpt = next((s for s in sentences if 'không phải giá cập nhật trực tiếp' in s), None)
            elif 'chỉnh ảnh' in query.casefold():
                excerpt = next((s for s in sentences if 'Với công việc đồ họa chuyên sâu' in s), None)
            else:
                excerpt = next((s for s in sentences if 'Chưa có benchmark' in s), None)
            if not excerpt:
                raise ValueError('Relevant FAQ excerpt missing')
            clauses.append(excerpt.rstrip('.'))
            refs.append(hit.source_ref)
        # Reuse only verified history from this viewer. Prefer new catalog facts
        # when an advisory answer would repeat all previously spoken statements.
        history = () if context is None else context.turns

        # Khi khách yêu cầu kết luận hoặc tổng hợp,
        # không loại bỏ những thông tin đã được kiểm chứng
        # chỉ vì chúng từng xuất hiện trong hội thoại.
        is_recap_request = any(
            term in query.casefold()
            for term in ('chốt lại', 'nên mua', 'nên chọn')
        )

        if intent == 'advisory' and history and not is_recap_request:
            prior = ' '.join(turn.answer.casefold() for turn in history)
            fresh = [clause for clause in clauses if clause.casefold() not in prior]
            if not fresh:
                fresh = [f"{products[sku]['brand']} có RAM {products[sku]['specifications']['ram']['capacity_gb']}GB" for sku in resolved_sku_ids]
            if 'excerpt' in locals() and excerpt.rstrip('.') not in fresh:
                refs.remove(hit.source_ref)
            clauses = fresh
        # Questions are fixed, claim-free suggestions checked by the verifier.
        # Avoid repeating the same question within this viewer's memory window.
        questions = {
            'price_inquiry': 'Bạn muốn mình tư vấn thêm về cấu hình của mẫu này không ạ?',
            'comparison': 'Bạn muốn tìm hiểu thêm về cấu hình của hai mẫu không ạ?',
            'advisory': 'Bạn ưu tiên màn hình hay khả năng nâng cấp về sau ạ?',
            'spec_inquiry': 'Bạn muốn tìm hiểu thêm về nhu cầu sử dụng nào không ạ?',
        }
        question = questions.get(intent)
        if question and not any(question in turn.answer for turn in history):
            clauses.append(question)
        text = '. '.join(part.rstrip('.').strip() for part in clauses)
        if not text.endswith('?'):
            text += '.'
        return CandidateAnswer(text, resolved_sku_ids, tuple(refs))


class ExperimentalOpenAISalesProvider:
    """Optional Responses API candidate generator; output is never trusted by itself."""

    def __init__(self, *, model: str, instructions: str, enabled: bool = False,
                 timeout_seconds: float = 20, client=None):
        if not model or not instructions or type(enabled) is not bool or timeout_seconds <= 0:
            raise ValueError('Invalid experimental sales provider configuration')
        self.model, self.instructions, self.enabled = model, instructions, enabled
        self.timeout_seconds, self._client = timeout_seconds, client

    @classmethod
    def from_files(cls, app_path, persona_path, *, client=None):
        app = yaml.safe_load(Path(app_path).read_text(encoding='utf-8'))
        persona = yaml.safe_load(Path(persona_path).read_text(encoding='utf-8'))
        return cls(model=app['llm']['model'], instructions=persona['instructions'],
                   enabled=persona['experimental_api_enabled'],
                   timeout_seconds=persona['timeout_seconds'], client=client)

    def generate(self, query: str, resolved_sku_ids: tuple[str, ...],
                 intent: str, evidence: EvidencePackage, *, context=None) -> CandidateAnswer:
        if not self.enabled:
            raise RuntimeError('EXPERIMENTAL_API_DISABLED')
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url='https://api.openai.com/v1',
                                  timeout=self.timeout_seconds, max_retries=0)
        plan = DeterministicProvider().generate(query, resolved_sku_ids, intent, evidence, context=context)
        if not AnswerVerifier().verify(plan, evidence, resolved_sku_ids, intent):
            raise ValueError('Factual plan did not pass verification')
        products = {e.sku_id: e.value for e in evidence.catalog_evidence
                    if e.field_path is None and isinstance(e.value, dict)}
        facts = {sku: {key: products[sku][key] for key in ('brand', 'model', 'price_vnd',
                 'stock_quantity', 'specifications')} for sku in resolved_sku_ids}
        history = [] if context is None else [{'question': t.question, 'answer': t.answer} for t in context.turns]
        data = {'viewer_question': query, 'intent': intent, 'resolved_sku_ids': resolved_sku_ids,
                'catalog_facts': facts, 'verified_fact_plan': plan.answer_text,
                'evidence_refs': plan.cited_evidence_refs, 'recent_context': history,
                'faq_evidence': [{'ref': h.source_ref, 'text': h.retrieval_text}
                    for h in evidence.faq_hits if h.metadata.get('needs_review') is False]}
        try:
            result = self._client.responses.create(model=self.model, instructions=self.instructions,
                input=json.dumps(data, ensure_ascii=False), max_output_tokens=500,
                timeout=self.timeout_seconds)
            payload = json.loads(result.output_text)
            if not isinstance(payload, dict) or set(payload) != {'answer_text', 'claimed_sku_ids', 'cited_evidence_refs', 'claims'}:
                raise ValueError('Invalid candidate fields')
            if not isinstance(payload['answer_text'], str) or not 1 <= len(payload['answer_text'].strip()) <= 500:
                raise ValueError('Invalid candidate text')
            for key in ('claimed_sku_ids', 'cited_evidence_refs', 'claims'):
                if not isinstance(payload[key], list) or any(not isinstance(x, str) for x in payload[key]):
                    raise ValueError('Invalid candidate list')
            return CandidateAnswer(payload['answer_text'], tuple(payload['claimed_sku_ids']),
                                   tuple(payload['cited_evidence_refs']), tuple(payload['claims']))
        except Exception:
            raise RuntimeError('EXPERIMENTAL_PROVIDER_FAILED') from None


# ============================================================
# 2. VERIFIED AGENT - ĐIỀU PHỐI VÀ ÁNH XẠ PUBLIC CONTRACT
# ============================================================

class VerifiedAgent:
    """
    Nối M01/M02 với provider và verifier để tạo public AgentResponse.

    ``engine``, memory, provider và verifier có thể được truyền từ ngoài để
    kiểm thử. Không sử dụng active_sku_id làm bằng chứng về sản phẩm khách hỏi.
    Memory chỉ cập nhật khi câu trả lời cuối cùng có trạng thái answered.
    """
    def __init__(self, engine, *, memory: ConversationMemory | None = None,
                 provider: LLMProvider | None = None, verifier: AnswerVerifier | None = None,
                 mode: str = "lexical", top_k: int = 5):
        self.engine = engine
        self.memory = memory if memory is not None else ConversationMemory()
        self.provider = provider if provider is not None else DeterministicProvider()
        self.verifier = verifier if verifier is not None else AnswerVerifier()
        self.mode, self.top_k = mode, top_k

    def process_queue_item(self, item: QueueItem) -> AgentResponse:
        """
        Nhận đầu ra queue M01 khi decision là selected và ID khớp event.

        Việc lọc spam, trùng lặp và quyết định chọn thuộc M01; gọi trực tiếp
        process_comment sẽ không tự thực hiện lại các bước triage đó.
        """
        if item.decision.action != "selected" or (item.event.run_id, item.event.comment_id) != (item.decision.run_id, item.decision.comment_id):
            raise ValueError("Queue item must have a matching selected decision")
        return self.process_comment(item.event)

    def process_comment(self, comment: CommentEvent) -> AgentResponse:
        """
        Xử lý một bình luận và ánh xạ kết quả sang public AgentResponse.

        Nội dung bị chặn không được đưa vào answer_text hoặc evidence_refs.
        Một SKU được ghi vào resolved_sku_id; câu trả lời nhiều SKU để None.
        """
        def response(status, reason=None, answer=None, refs=(), sku=None):
            return AgentResponse(response_id="RESP-" + uuid4().hex, comment_id=comment.comment_id,
                run_id=comment.run_id, viewer_id=comment.viewer_id, resolved_sku_id=sku,
                status=status, reason_code=reason, answer_text=answer, evidence_refs=refs,
                created_at=datetime.now(timezone.utc))
        # 1. Chặn một số yêu cầu vượt phạm vi hoặc có dấu hiệu nguy hiểm.
        # Đây là heuristic theo từ khóa, có thể bỏ sót hoặc chặn nhầm.
        text = comment.text.casefold()
        duration = bool(re.search(r"\b(?:\d+|mấy|bao nhiêu)\s*(?:tiếng|giờ)\b", text))
        if duration or any(x in text for x in ("bỏ qua", "ignore previous", "system prompt", "jailbreak", "bịa", "thời tiết", "nấu phở", "fps", "trả góp", "khuyến mãi", "freeship", "đặt hàng", "chốt đơn", "lên đơn", "giờ pin", "pin bao lâu", "giảm", "ưu đãi", "đặt asus", "đặt lenovo")):
            return response("blocked", "UNSUPPORTED_REQUEST")
        if any(x in text for x in ("macbook", "dell", "acer")):
            return response("clarification_needed", "PRODUCT_NOT_FOUND", "Demo hiện chỉ có ASUS và Lenovo; bạn muốn hỏi mẫu nào?")
        # 2. SKU nêu rõ được ưu tiên. Chỉ kế thừa memory khi có dấu hiệu nối tiếp;
        # so sánh khuyết một vế cần đủ hai SKU khác nhau, không đoán active SKU.
        context = self.memory.get_context(comment.run_id, comment.viewer_id)
        explicit = tuple(s for s, terms in (("LAPTOP-ASUS-001", ("asus", "vivobook", "s5406")),
                         ("LAPTOP-LENOVO-002", ("lenovo", "xiaoxin", "ideapad"))) if any(t in text for t in terms))
        advice = any(x in text for x in ("docker", "máy ảo", "học it", "chỉnh ảnh", "nên chọn", "nên mua"))
        comparison = advice or any(x in text for x in ("so sánh", "so với", "máy nào", "con nào", "chênh"))
        followup = any(re.search(rf"\b{re.escape(x)}\b", text) for x in ("vậy", "thế", "máy này", "máy đó", "con này", "con đó", "nếu", "còn"))
        if comparison:
            if "so với" in text and not advice and len(explicit) == 1:
                skus = tuple(dict.fromkeys(context.last_resolved_sku_ids + explicit))
                if len(skus) != 2:
                    return response("clarification_needed", "REFERENCE_AMBIGUOUS", "Bạn muốn so sánh ASUS với Lenovo ạ?")
            else:
                skus = ("LAPTOP-ASUS-001", "LAPTOP-LENOVO-002")
        else:
            skus = explicit or (context.last_resolved_sku_ids if followup else ())
        if not skus:
            return response("clarification_needed", "REFERENCE_AMBIGUOUS", "Bạn muốn hỏi mẫu ASUS hay Lenovo ạ?")
        # 3. Chọn intent bằng quy tắc hiện có; intent chưa hỗ trợ sẽ bị chặn.
        if advice or (comparison and not any(x in text for x in ("giá", "chênh", "tiền"))):
            intent = "advisory"
        elif comparison:
            intent = "comparison"
        elif any(x in text for x in ("nâng", "upgrade")):
            intent = "upgrade_inquiry"
        elif "giá" in text and any(x in text for x in ("website", "trang web", "web")):
            intent = "price_discrepancy"
        elif any(x in text for x in ("giá", "bao nhiêu tiền")):
            intent = "price_inquiry"
        elif any(x in text for x in ("tồn kho", "còn hàng", "còn máy")):
            intent = "stock_inquiry"
        elif any(x in text for x in ("màn hình", "màn oled", "pin", "ram", "ssd", "cpu", "chip")):
            intent = "spec_inquiry"
        else:
            return response("blocked", "UNSUPPORTED_REQUEST")
        # 4. Lấy catalog theo SKU đã xác định trước, rồi truy xuất FAQ/evidence.
        # Tách hai khối để phân biệt lỗi catalog với lỗi retrieval/provider.
        try:
            facts = tuple(self.engine.get_catalog_evidence(sku) for sku in skus)
        except (OSError, ValueError, KeyError, TypeError):
            return response("blocked", "CATALOG_UNAVAILABLE")
        except Exception:
            return response("blocked", "INTERNAL_ERROR")
        try:
            package = self.engine.retrieve(comment.text, mode=self.mode, top_k=self.top_k, sku_ids=skus)
        except Exception:
            return response("blocked", "INTERNAL_ERROR")
        if package.status != "ok":
            if package.reason in ('AMBIGUOUS_SKU', 'SKU_REQUIRED'):
                return response("clarification_needed", "REFERENCE_AMBIGUOUS", "Bạn muốn hỏi mẫu ASUS hay Lenovo ạ?")
            return response("blocked", "UNSUPPORTED_REQUEST")
        # M02 có thể trả evidence theo từng trường; thêm bản ghi catalog đầy đủ
        # để provider và verifier đối chiếu các fact được hỗ trợ.
        package = replace(package, catalog_evidence=package.catalog_evidence + facts)
        try:
            if isinstance(self.provider, ExperimentalOpenAISalesProvider):
                try:
                    candidate = self.provider.generate(comment.text, skus, intent, package, context=context)
                    if not self.verifier.verify(candidate, package, skus, intent):
                        raise ValueError('Experimental candidate not verified')
                except Exception:
                    candidate = DeterministicProvider().generate(comment.text, skus, intent, package, context=context)
            elif isinstance(self.provider, DeterministicProvider):
                candidate = self.provider.generate(comment.text, skus, intent, package, context=context)
            else:
                candidate = self.provider.generate(comment.text, skus, intent, package)
            if not isinstance(candidate, CandidateAnswer):
                return response("blocked", "INTERNAL_ERROR")
            if not self.verifier.verify(candidate, package, skus, intent):
                return response("blocked", "VERIFICATION_FAILED")
            result = response("answered", answer=candidate.answer_text, refs=candidate.cited_evidence_refs,
                              sku=skus[0] if len(skus) == 1 else None)
        except Exception:
            return response("blocked", "INTERNAL_ERROR")
        # 5. Chỉ lưu ngữ cảnh sau khi candidate đã qua verifier và tạo response.
        self.memory.update_context(comment.run_id, comment.viewer_id, resolved_sku_ids=skus,
                                   intent=intent, question=comment.text, answer=result.answer_text)
        return result


# ============================================================
# 3. SERIALIZATION - CHỈ GHI FILE KHI ĐƯỢC GỌI TƯỜNG MINH
# ============================================================

def serialize_responses(responses: list[AgentResponse], path: str | Path) -> None:
    """
    Ghi danh sách AgentResponse thành JSON UTF-8 khi caller chủ động gọi.

    Hàm tạo thư mục cha nếu cần và có thể ghi đè file đích đã tồn tại;
    caller chịu trách nhiệm chọn đường dẫn phù hợp với run và chính sách lưu trữ.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps([item.model_dump(mode="json") for item in responses],
                                      ensure_ascii=False, indent=2), encoding="utf-8")
