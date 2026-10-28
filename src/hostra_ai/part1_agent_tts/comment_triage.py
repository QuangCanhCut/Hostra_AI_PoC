"""Phân loại bình luận bằng các quy tắc xác định và thận trọng."""

import re
from datetime import datetime, timedelta

from hostra_ai.core.schemas import CommentDecision, CommentEvent
from .comment_decisions import make_decision
from .comment_policy import CommentPolicy


def normalize_text(text: str) -> str:
    """Gộp khoảng trắng và bỏ phân biệt hoa/thường, vẫn giữ dấu tiếng Việt.

    Chỉ dùng bản này để so sánh; không thay nội dung trong CommentEvent.
    """
    return " ".join(text.split()).casefold()


# Từ khóa gợi ý ý định; mỗi nhóm khớp được cộng điểm một lần, không phải suy luận LLM.
INTENTS = {
    "price": ("giá", "bao nhiêu", "giảm", "ưu đãi"),
    "technical": ("ram", "ssd", "cpu", "gpu", "màn hình", "oled", "pin", "fps", "benchmark", "thông số"),
    "comparison": ("so với", "so sánh", "chênh nhau"),
    "advice": ("nên chọn", "nên mua", "nhu cầu", "tư vấn", "máy ảo", "docker"),
    "purchase": ("đặt hàng", "đặt thế nào", "muốn đặt", "trả góp", "mua hàng", "chốt"),
    "follow_up": ("vậy", "thế", "máy này", "máy đó", "nếu"),
}
PRODUCT_TERMS = ("laptop", "máy", "asus", "lenovo", "ram", "ssd", "giá", "mua", "shop", "đặt", "trả góp", "pin", "cpu", "gpu", "màn hình")
OFF_TOPIC_TERMS = ("cầu thủ", "bóng đá", "trận đấu", "bàn thắng", "ghi nhiều bàn")


def score_comment(text: str, policy: CommentPolicy) -> int:
    """Cộng điểm cơ sở và trọng số các nhóm khớp, giới hạn kết quả ở 100."""
    normalized = normalize_text(text)
    return min(100, policy.scores["base"] + sum(
        policy.scores[group] for group, terms in INTENTS.items()
        if any(term in normalized for term in terms)))


def is_spam(text: str) -> bool:
    """Nhận diện tín hiệu spam rõ ràng; chữ in hoa đơn lẻ không đủ kết luận."""
    normalized = normalize_text(text)
    # Chỉ kết luận spam khi từ "spam" xuất hiện ít nhất hai lần.
    return len(re.findall(r"\bspam\b", normalized)) >= 2


def is_off_topic(text: str) -> bool:
    """Bỏ qua dấu hiệu bóng đá rõ ràng khi không có từ liên quan bán laptop."""
    normalized = normalize_text(text)
    return (any(term in normalized for term in OFF_TOPIC_TERMS)
            and not any(term in normalized for term in PRODUCT_TERMS))


class CommentTriage:
    """Giữ lịch sử so sánh duplicate và tạo quyết định cho từng bình luận."""
    def __init__(self, policy: CommentPolicy):
        self.policy = policy
        # Khóa lịch sử gồm phiên, người xem và nội dung đã chuẩn hóa.
        self._history: dict[tuple[str, str, str], list[CommentEvent]] = {}
        self._last_time: datetime | None = None

    def evaluate(self, event: CommentEvent, *, now: datetime | None = None) -> CommentDecision:
        """Đánh giá sự kiện theo thứ tự thời gian; mặc định dùng giờ nhận làm giờ quyết định.

        Thứ tự kiểm tra là duplicate, spam, off-topic; còn lại được selected.
        """
        now = event.received_at if now is None else now
        if now.tzinfo is None or now.utcoffset() is None or now < event.received_at:
            raise ValueError("now must be timezone-aware and not before received_at")
        if self._last_time is not None and event.received_at < self._last_time:
            raise ValueError("triage events must be in chronological order")
        self._last_time = event.received_at
        key = (event.run_id, event.viewer_id, normalize_text(event.text))
        history = self._history.setdefault(key, [])
        window = timedelta(seconds=self.policy.duplicate_seconds)
        # Chọn bản cũ nhất còn trong cửa sổ, kể cả bản từng bị đánh dấu trùng.
        # Không so bình luận với chính nó khi cùng sự kiện được đánh giá lại.
        match = next((prior for prior in history if prior.comment_id != event.comment_id
                      and timedelta(0) <= event.received_at - prior.received_at <= window), None)
        if not any(prior.comment_id == event.comment_id for prior in history):
            history.append(event)
        score = score_comment(event.text, self.policy)
        reason = "DUPLICATE" if match else "SPAM" if is_spam(event.text) else "OFF_TOPIC" if is_off_topic(event.text) else None
        return make_decision(event, action="skipped" if reason else "selected", reason=reason,
                             score=score, policy_version=self.policy.version, now=now,
                             duplicate_of=match.comment_id if match else None)
