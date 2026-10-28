"""Quản lý hàng đợi trong bộ nhớ, thứ tự ưu tiên và vòng đời deferred."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from hostra_ai.core.schemas import CommentDecision, CommentEvent
from .comment_decisions import make_decision
from .comment_policy import CommentPolicy


@dataclass(frozen=True)
class QueueItem:
    """Bình luận cùng quyết định hiện hành và số thứ tự dùng để đảm bảo FIFO."""
    event: CommentEvent
    decision: CommentDecision
    sequence: int


class CommentQueue:
    """Nhận, trì hoãn và bàn giao bình luận theo đồng hồ mô phỏng.

    Bên gọi chủ động gọi reevaluate khi thời gian tiến và pop khi bàn giao.
    State chỉ lưu trong bộ nhớ; lớp này không tự chạy nền hoặc phát âm thanh.
    """
    def __init__(self, policy: CommentPolicy):
        self.policy = policy
        # Mỗi khóa là (run_id, comment_id); terminal ngăn nhận lại mục đã kết thúc.
        self._ready: dict[tuple[str, str], QueueItem] = {}
        self._deferred: dict[tuple[str, str], QueueItem] = {}
        self._terminal: set[tuple[str, str]] = set()
        self._sequence = 0
        self._last_viewer: str | None = None
        self._consecutive = 0
        self._clock: datetime | None = None
        self.decisions: list[CommentDecision] = []

    def _advance(self, now: datetime) -> None:
        """Bảo đảm đồng hồ có múi giờ và không lùi trong cùng phiên mô phỏng."""
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        if self._clock is not None and now < self._clock:
            raise ValueError("simulation clock cannot move backwards")
        self._clock = now

    @staticmethod
    def _key(event: CommentEvent) -> tuple[str, str]:
        """Định danh bình luận trong phạm vi phiên."""
        return event.run_id, event.comment_id

    def _decision(self, item: QueueItem, action: str, reason: str | None, now: datetime) -> CommentDecision:
        """Tạo quyết định mới khi trạng thái queue thay đổi, giữ lại điểm ban đầu."""
        return make_decision(item.event, action=action, reason=reason,
                             score=item.decision.priority_score,
                             policy_version=self.policy.version, now=now)

    def admit(self, event: CommentEvent, decision: CommentDecision, *, now: datetime) -> CommentDecision:
        """Nhận cặp sự kiện/quyết định; nếu queue đầy thì chuyển selected sang deferred.

        Trả quyết định hiện hành; lịch sử bao gồm cả quyết định trước khi chuyển trạng thái.
        """
        self._advance(now)
        if now < event.received_at or now < decision.decided_at:
            raise ValueError("now precedes event or decision")
        if (decision.run_id, decision.comment_id) != self._key(event):
            raise ValueError("decision does not match event")
        if decision.policy_version != self.policy.version:
            raise ValueError("decision policy does not match queue policy")
        key = self._key(event)
        if key in self._ready or key in self._deferred or key in self._terminal:
            raise ValueError("comment already admitted or processed")
        self.decisions.append(decision)
        item = QueueItem(event, decision, self._sequence)
        self._sequence += 1
        if decision.action == "selected":
            if len(self._ready) < self.policy.max_queue_size:
                self._ready[key] = item
            else:
                decision = self._decision(item, "deferred", "QUEUE_BUSY", now)
                self.decisions.append(decision)
                self._deferred[key] = QueueItem(event, decision, item.sequence)
        elif decision.action == "deferred":
            self._deferred[key] = item
        else:
            self._terminal.add(key)
        return decision

    def reevaluate(self, *, now: datetime) -> list[CommentDecision]:
        """Hết hạn các mục chờ rồi đưa mục còn hạn vào chỗ trống theo điểm/FIFO.

        TTL tính từ received_at và hết hạn ngay tại biên; trả các quyết định mới.
        """
        self._advance(now)
        changes: list[CommentDecision] = []
        # Xử lý hết hạn trước để mục quá TTL không được chọn lại khi queue vừa có chỗ.
        for key, item in list(self._deferred.items()):
            if now >= item.event.received_at + timedelta(seconds=self.policy.deferred_seconds):
                decision = self._decision(item, "skipped", "EXPIRED", now)
                changes.append(decision)
                del self._deferred[key]
                self._terminal.add(key)
        candidates = sorted(self._deferred.items(), key=lambda pair: (-pair[1].decision.priority_score, pair[1].sequence))
        for key, item in candidates:
            if len(self._ready) >= self.policy.max_queue_size:
                break
            decision = self._decision(item, "selected", None, now)
            changes.append(decision)
            self._ready[key] = QueueItem(item.event, decision, item.sequence)
            del self._deferred[key]
        self.decisions.extend(changes)
        return changes

    def pop(self, *, now: datetime) -> QueueItem | None:
        """Bàn giao một mục sẵn sàng, ưu tiên điểm cao rồi FIFO khi bằng điểm.

        Khi một viewer đã đạt số lượt liên tiếp tối đa và có viewer khác đang chờ,
        chọn trong nhóm viewer khác để tránh một người chiếm toàn bộ lượt.
        """
        self._advance(now)
        if not self._ready:
            return None
        candidates = list(self._ready.values())
        if self._consecutive >= self.policy.max_consecutive_per_viewer:
            others = [item for item in candidates if item.event.viewer_id != self._last_viewer]
            if others:
                candidates = others
        item = min(candidates, key=lambda value: (-value.decision.priority_score, value.sequence))
        del self._ready[self._key(item.event)]
        self._terminal.add(self._key(item.event))
        if item.event.viewer_id == self._last_viewer:
            self._consecutive += 1
        else:
            self._last_viewer, self._consecutive = item.event.viewer_id, 1
        return item

    @property
    def ready_count(self) -> int:
        """Số bình luận đang sẵn sàng bàn giao."""
        return len(self._ready)

    @property
    def deferred_count(self) -> int:
        """Số bình luận đang chờ đánh giá lại."""
        return len(self._deferred)
