"""
M03 - Bộ nhớ hội thoại trong RAM cho Verified Sales Agent.

Ngữ cảnh được định danh bằng ``(run_id, viewer_id)``. Agent dùng ngữ cảnh
để hiểu câu nối tiếp như "vậy máy đó thì sao?", thay vì tự suy ra từ SKU
đang được giới thiệu trên livestream.

Bộ nhớ chỉ tồn tại trong tiến trình hiện tại, không tự hết hạn hay chia sẻ
giữa các tiến trình. VerifiedAgent chịu trách nhiệm chỉ cập nhật sau khi
câu trả lời đã được chấp nhận; lớp này không tự kiểm chứng nội dung.
"""
from dataclasses import dataclass


# ============================================================
# 1. DỮ LIỆU NGỮ CẢNH - LƯU THEO TỪNG RUN VÀ VIEWER
# ============================================================

@dataclass(frozen=True)
class ConversationTurn:
    """Một cặp câu hỏi và câu trả lời đã được agent lưu lại."""
    question: str
    answer: str


@dataclass(frozen=True)
class ConversationContext:
    """
    Ảnh chụp ngữ cảnh gần nhất của một viewer trong một run.

    ``last_resolved_sku_ids`` là sản phẩm khách hỏi, có thể gồm hai SKU khi
    so sánh. ``turns`` lưu lịch sử từ cũ đến mới. Tuple và dataclass frozen
    giúp caller không sửa trực tiếp trạng thái đã lưu.
    """
    last_resolved_sku_ids: tuple[str, ...] = ()
    last_intent: str | None = None
    turns: tuple[ConversationTurn, ...] = ()


# ============================================================
# 2. QUẢN LÝ VÒNG ĐỜI VÀ GIỚI HẠN LỊCH SỬ
# ============================================================

class ConversationMemory:
    """
    Quản lý ngữ cảnh độc lập và giới hạn số lượt cho từng cặp run/viewer.

    Khi vượt giới hạn, lượt cũ nhất bị bỏ theo cơ chế cửa sổ trượt. Giới hạn
    này không hạn chế tổng số viewer hoặc tổng số run trong bộ nhớ.
    """
    def __init__(self, max_turns_per_viewer: int = 5):
        if max_turns_per_viewer < 1:
            raise ValueError("max_turns_per_viewer must be positive")
        self.max_turns_per_viewer = max_turns_per_viewer
        self._contexts: dict[tuple[str, str], ConversationContext] = {}

    def get_context(self, run_id: str, viewer_id: str) -> ConversationContext:
        """Lấy ngữ cảnh hiện có; trả ngữ cảnh rỗng nếu chưa có lượt được lưu."""
        return self._contexts.get((run_id, viewer_id), ConversationContext())

    def update_context(self, run_id: str, viewer_id: str, *, resolved_sku_ids: tuple[str, ...],
                       intent: str, question: str, answer: str) -> None:
        """
        Lưu SKU, intent và cặp hỏi–đáp mới, đồng thời cắt bớt lịch sử cũ.

        Hàm tin dữ liệu do caller truyền vào. Không gọi cho lượt bị chặn,
        cần làm rõ hoặc gặp lỗi nếu không muốn làm bẩn ngữ cảnh trước đó.
        """
        previous = self.get_context(run_id, viewer_id)
        turns = (previous.turns + (ConversationTurn(question, answer),))[-self.max_turns_per_viewer:]
        self._contexts[(run_id, viewer_id)] = ConversationContext(tuple(resolved_sku_ids), intent, turns)

    def clear_viewer(self, run_id: str, viewer_id: str) -> None:
        """Xóa ngữ cảnh của một viewer trong một run."""
        self._contexts.pop((run_id, viewer_id), None)

    def clear_run(self, run_id: str) -> None:
        """Xóa mọi ngữ cảnh thuộc run; không ảnh hưởng các run khác."""
        for key in tuple(self._contexts):
            if key[0] == run_id:
                del self._contexts[key]
