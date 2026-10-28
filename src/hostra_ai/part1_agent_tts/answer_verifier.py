"""Independent, conservative verification of candidate answers against evidence."""
from dataclasses import dataclass
import re

from .knowledge.models import EvidencePackage


@dataclass(frozen=True)
class CandidateAnswer:
    answer_text: str
    claimed_sku_ids: tuple[str, ...]
    cited_evidence_refs: tuple[str, ...]
    claims: tuple[str, ...] = ()


class AnswerVerifier:
    """Verify structured catalog facts and cited FAQ excerpts; reject unknown prose.

    This intentionally supports a limited grammar: unknown factual assertions cannot
    be validated reliably by checking only numbers and citations.
    """
    def verify(self, candidate: CandidateAnswer, evidence: EvidencePackage,
               resolved_sku_ids: tuple[str, ...], intent: str) -> bool:
        if not isinstance(candidate, CandidateAnswer) or not resolved_sku_ids:
            return False
        if candidate.claimed_sku_ids != resolved_sku_ids or not candidate.answer_text.strip():
            return False
        refs = candidate.cited_evidence_refs
        if not refs or len(refs) > 10 or len(set(refs)) != len(refs):
            return False
        products = {e.sku_id: e.value for e in evidence.catalog_evidence
                    if e.field_path is None and isinstance(e.value, dict)
                    and e.source_ref == f"catalog:{e.sku_id}"}
        required = {f"catalog:{sku}" for sku in resolved_sku_ids}
        if not required.issubset(refs) or any(sku not in products for sku in resolved_sku_ids):
            return False
        hits = {h.source_ref: h for h in evidence.faq_hits
                if h.source_ref == f"faq:{h.metadata.get('faq_id')}"}
        for ref in refs:
            if ref in required:
                continue
            hit = hits.get(ref)
            if hit is None or hit.metadata.get("needs_review") is not False:
                return False
        if any(not isinstance(c, str) or c not in candidate.answer_text for c in candidate.claims):
            return False

        text = candidate.answer_text.strip()
        # Delimit clauses without splitting decimal separators in prices or model names.
        clauses = [s.strip(" ,;.") for s in re.split(r"[;\n]|(?<!\d)\.(?=\s|$)", text) if s.strip(" ,;.")]
        if not clauses:
            return False
        for clause in clauses:
            if not self._check_clause(clause, products, resolved_sku_ids, refs, hits):
                return False
        return True

    @staticmethod
    def _check_clause(clause, products, skus, refs, hits):
        t = " ".join(clause.casefold().split())
        # Accept refusals only when the entire clause is a refusal, not a mixed claim.
        if re.fullmatch(r"(?:em |mình )?chưa thể cam kết (?:số )?fps hoặc (?:số giờ|thời lượng) pin", t):
            return True
        if re.search(r"\bfps\b|\b\d+\s*(?:tiếng|giờ)\b|trả góp|khuyến mãi|freeship|đã (?:lên|chốt|đặt) đơn", t):
            return False

        if t == "giá em vừa nêu là giá được cấu hình cho phiên demo hostra, không phải giá cập nhật trực tiếp từ trang bán hàng":
            return any(ref in hits and hits[ref].metadata.get('faq_id') == 'FAQ-SALES-005'
                       and t in hits[ref].retrieval_text.replace('**', '').casefold() for ref in refs)

        # FAQ can only contribute verbatim answer excerpts (not the query/title).
        # Numeric or commercial assertions require independent catalog validation.
        if not re.search(r"\d|\b(?:giá|ram|ssd|pin|oled|ips|bảo hành|nâng cấp|hàng|giảm)\b", t):
            for ref in refs:
                if ref not in hits:
                    continue
                lines = hits[ref].retrieval_text.splitlines()
                allowed = ("chưa có benchmark cùng điều kiện nên em không kết luận máy nào chạy code nhanh hơn toàn diện",
                           "với công việc đồ họa chuyên sâu, nên xem yêu cầu phần mềm cụ thể trước khi quyết định")
                if t in allowed and len(lines) >= 3 and t in lines[-1].replace("**", "").casefold():
                    return True

        for sku in skus:
            p = products[sku]
            name = str(p.get("brand", "")).casefold()
            if not name or not re.search(rf"\b{re.escape(name)}\b", t):
                continue
            # Multiple product names in one clause are handled only as a difference.
            if any(other != sku and re.search(rf"\b{re.escape(str(products[other]['brand']).casefold())}\b", t) for other in skus):
                continue
            price = f"{p['price_vnd']:,}".replace(",", ".")
            if re.fullmatch(rf"(?:giá\s+)?{re.escape(name)}(?:\s+trong phiên demo hostra)?(?:\s*:\s*|\s+(?:là|có giá)\s+){re.escape(price)}\s*(?:đồng|vnđ)(?:\s+trong phiên demo hostra)?", t):
                return "demo hostra" in t
            if re.fullmatch(rf"{re.escape(name)}\s*:\s*{p['stock_quantity']}\s+máy\s+trong phiên demo hostra", t):
                return True
            for field, label in (("ram", "ram"), ("storage", "ssd")):
                value = p["specifications"][field]["upgradable"]
                expected = "chưa xác nhận khả năng nâng cấp" if value is None else "có thể nâng cấp" if value else "không thể nâng cấp"
                if t == f"{name}: {label} {expected}":
                    return True
            display = p["specifications"]["display"]
            if display.get("panel") is not None and t == f"{name}: màn hình {display['panel'].casefold()}, {display['refresh_rate_hz']}hz":
                return True
            if display.get("panel") is None and t == f"{name}: chưa xác nhận tấm nền màn hình":
                return True
            if t == f"{name}: pin {p['specifications']['battery_wh']}wh":
                return True
            if t == f"{name}: ram {p['specifications']['ram']['capacity_gb']}gb":
                return True
            if t == f"{name}: ssd {p['specifications']['storage']['capacity_label'].casefold()}":
                return True
            if t == f"{name}: cpu {p['specifications']['cpu']['model'].casefold()}":
                return True
        if len(skus) == 2:
            a, b = (products[sku] for sku in skus)
            cheaper, dearer = sorted((a, b), key=lambda p: p['price_vnd'])
            diff = f"{dearer['price_vnd'] - cheaper['price_vnd']:,}".replace(",", ".")
            if t == f"{cheaper['brand'].casefold()} rẻ hơn {dearer['brand'].casefold()} {diff} đồng trong phiên demo hostra":
                return True
        return False
