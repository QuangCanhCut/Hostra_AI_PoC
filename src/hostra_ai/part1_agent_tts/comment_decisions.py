"""Tạo quyết định theo contract với định danh riêng cho mỗi lần đánh giá."""

from datetime import datetime
from uuid import uuid4

from hostra_ai.core.schemas import CommentDecision, CommentEvent


def make_decision(event: CommentEvent, *, action: str, reason: str | None,
                  score: int, policy_version: str, now: datetime,
                  duplicate_of: str | None = None) -> CommentDecision:
    """Tạo CommentDecision; contract kiểm tra action, reason và múi giờ.

    UUID giúp phân biệt các quyết định khi cùng bình luận được đánh giá lại.
    Thời điểm now do bên gọi cung cấp để có thể mô phỏng và kiểm thử.
    """
    return CommentDecision(decision_id=f"DEC-{uuid4().hex}", run_id=event.run_id,
        comment_id=event.comment_id, action=action, reason_code=reason,
        priority_score=score, duplicate_of=duplicate_of,
        policy_version=policy_version, decided_at=now)
