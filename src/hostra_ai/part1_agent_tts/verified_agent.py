"""Offline sales-agent orchestration with conservative, catalog-backed output."""
from dataclasses import replace
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from hostra_ai.core.schemas import AgentResponse, CommentEvent
from .answer_verifier import AnswerVerifier, CandidateAnswer
from .conversation_memory import ConversationMemory
from .comment_queue import QueueItem
from .knowledge.models import EvidencePackage


class LLMProvider(Protocol):
    def generate(self, query: str, resolved_sku_ids: tuple[str, ...],
                 intent: str, evidence: EvidencePackage) -> CandidateAnswer: ...


class DeterministicProvider:
    def generate(self, query: str, resolved_sku_ids: tuple[str, ...],
                 intent: str, evidence: EvidencePackage) -> CandidateAnswer:
        products = {item.sku_id: item.value for item in evidence.catalog_evidence if item.field_path is None}
        clauses = []
        for sku in resolved_sku_ids:
            p = products[sku]
            name = p['brand']
            specs = p['specifications']
            if intent in ('price_inquiry', 'comparison', 'price_discrepancy'):
                price = f"{p['price_vnd']:,}".replace(',', '.')
                clauses.append(f"{name}: {price} đồng trong phiên demo HOSTRA")
            elif intent == 'stock_inquiry':
                clauses.append(f"{name}: {p['stock_quantity']} máy trong phiên demo HOSTRA")
            elif intent in ('upgrade_inquiry', 'advisory'):
                if intent == 'advisory' and 'chỉnh ảnh' in query.casefold() and specs['display'].get('panel'):
                    clauses.append(f"{name}: màn hình {specs['display']['panel']}, {specs['display']['refresh_rate_hz']}Hz")
                for field, label in (('ram', 'RAM'), ('storage', 'SSD')):
                    val = specs[field]['upgradable']
                    state = 'chưa xác nhận khả năng nâng cấp' if val is None else 'có thể nâng cấp' if val else 'không thể nâng cấp'
                    clauses.append(f'{name}: {label} {state}')
            elif intent == 'spec_inquiry':
                q = query.casefold()
                if 'pin' in q:
                    clauses.append(f"{name}: pin {specs['battery_wh']}Wh")
                elif 'ram' in q:
                    clauses.append(f"{name}: RAM {specs['ram']['capacity_gb']}GB")
                elif 'ssd' in q:
                    clauses.append(f"{name}: SSD {specs['storage']['capacity_label']}")
                elif 'cpu' in q or 'chip' in q:
                    clauses.append(f"{name}: CPU {specs['cpu']['model']}")
                elif specs['display'].get('panel'):
                    display = specs['display']
                    clauses.append(f"{name}: màn hình {display['panel']}, {display['refresh_rate_hz']}Hz")
                else:
                    clauses.append(f'{name}: chưa xác nhận tấm nền màn hình')
            else:
                raise ValueError('Unsupported intent')
        if intent == 'comparison' and len(resolved_sku_ids) == 2:
            cheaper, dearer = sorted((products[s] for s in resolved_sku_ids), key=lambda p: p['price_vnd'])
            diff = f"{dearer['price_vnd'] - cheaper['price_vnd']:,}".replace(',', '.')
            clauses.append(f"{cheaper['brand']} rẻ hơn {dearer['brand']} {diff} đồng trong phiên demo HOSTRA")
        refs = [f'catalog:{sku}' for sku in resolved_sku_ids]
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
        return CandidateAnswer('; '.join(clauses) + '.', resolved_sku_ids, tuple(refs))


class VerifiedAgent:
    def __init__(self, engine, *, memory: ConversationMemory | None = None,
                 provider: LLMProvider | None = None, verifier: AnswerVerifier | None = None,
                 mode: str = "lexical", top_k: int = 5):
        self.engine = engine
        self.memory = memory if memory is not None else ConversationMemory()
        self.provider = provider if provider is not None else DeterministicProvider()
        self.verifier = verifier if verifier is not None else AnswerVerifier()
        self.mode, self.top_k = mode, top_k

    def process_queue_item(self, item: QueueItem) -> AgentResponse:
        if item.decision.action != "selected" or (item.event.run_id, item.event.comment_id) != (item.decision.run_id, item.decision.comment_id):
            raise ValueError("Queue item must have a matching selected decision")
        return self.process_comment(item.event)

    def process_comment(self, comment: CommentEvent) -> AgentResponse:
        def response(status, reason=None, answer=None, refs=(), sku=None):
            return AgentResponse(response_id="RESP-" + uuid4().hex, comment_id=comment.comment_id,
                run_id=comment.run_id, viewer_id=comment.viewer_id, resolved_sku_id=sku,
                status=status, reason_code=reason, answer_text=answer, evidence_refs=refs,
                created_at=datetime.now(timezone.utc))
        text = comment.text.casefold()
        duration = bool(re.search(r"\b(?:\d+|mấy|bao nhiêu)\s*(?:tiếng|giờ)\b", text))
        if duration or any(x in text for x in ("bỏ qua", "ignore previous", "system prompt", "jailbreak", "bịa", "thời tiết", "nấu phở", "fps", "trả góp", "khuyến mãi", "freeship", "đặt hàng", "chốt đơn", "lên đơn", "giờ pin", "pin bao lâu", "giảm", "ưu đãi", "đặt asus", "đặt lenovo")):
            return response("blocked", "UNSUPPORTED_REQUEST")
        if any(x in text for x in ("macbook", "dell", "acer")):
            return response("clarification_needed", "PRODUCT_NOT_FOUND", "Demo hiện chỉ có ASUS và Lenovo; bạn muốn hỏi mẫu nào?")
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
        package = replace(package, catalog_evidence=package.catalog_evidence + facts)
        try:
            candidate = self.provider.generate(comment.text, skus, intent, package)
            if not isinstance(candidate, CandidateAnswer):
                return response("blocked", "INTERNAL_ERROR")
            if not self.verifier.verify(candidate, package, skus, intent):
                return response("blocked", "VERIFICATION_FAILED")
            result = response("answered", answer=candidate.answer_text, refs=candidate.cited_evidence_refs,
                              sku=skus[0] if len(skus) == 1 else None)
        except Exception:
            return response("blocked", "INTERNAL_ERROR")
        self.memory.update_context(comment.run_id, comment.viewer_id, resolved_sku_ids=skus,
                                   intent=intent, question=comment.text, answer=result.answer_text)
        return result


def serialize_responses(responses: list[AgentResponse], path: str | Path) -> None:
    """Write responses only when explicitly requested by the caller."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps([item.model_dump(mode="json") for item in responses],
                                      ensure_ascii=False, indent=2), encoding="utf-8")
