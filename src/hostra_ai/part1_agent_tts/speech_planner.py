"""
M04 - Lập lượt nói và kiểm tra điều kiện đưa lượt đó vào TTS.

SpeechPlanner chuyển AgentResponse hoặc script thành SpeechTurn có thể truy vết.
SpeechAdmission kiểm tra nguồn, SKU, hạn và trùng lặp trước khi cho tổng hợp.
Hai lớp chỉ làm việc trong bộ nhớ của tiến trình hiện tại; không thay thế
scheduler cuối, không quyết định timestamp hoặc tránh chồng âm thanh trên video.

Quan trọng: AgentResponse là ranh giới tin cậy từ M03. Planner kiểm tra cấu
trúc nhưng không tự chạy lại AnswerVerifier để chứng minh nội dung phản hồi.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Callable
from uuid import uuid4

from hostra_ai.core.schemas.part1 import AgentResponse, SpeechTurn


# ============================================================
# 1. SPEECH PLANNER - NGUỒN NỘI DUNG VÀ PHÊ DUYỆT SCRIPT
# ============================================================

class PlanningError(ValueError):
    """Nguồn nội dung hoặc lượt nói không đáp ứng điều kiện lập kế hoạch."""


class SpeechPlanner:
    """
    Tạo SpeechTurn từ response hợp lệ hoặc script đã có thông tin phê duyệt.

    ``scripts`` là dữ liệu thư viện trong bộ nhớ. ``check_script`` là callback
    do caller cung cấp để kiểm tra điều kiện sử dụng/evidence khi script có
    các trường đó; không có callback phù hợp thì script bị từ chối.

    Danh sách ``_issued`` giúp admission nhận biết chính xác turn do instance
    này tạo. Đây là kiểm tra trong tiến trình, không phải cơ chế xác thực
    chống lại mã độc cùng tiến trình hoặc bộ nhớ lưu bền sau khi khởi động lại.
    """
    def __init__(self, scripts: dict, *, priorities: dict | None = None,
                 check_script: Callable[[dict], bool] | None = None):
        if not isinstance(scripts, dict) or not isinstance(scripts.get('scripts'), list):
            raise PlanningError('INVALID_SCRIPT_LIBRARY')
        self._scripts = {}
        for script in scripts['scripts']:
            if not isinstance(script, dict) or not isinstance(script.get('script_id'), str) or not script['script_id'].strip():
                raise PlanningError('INVALID_SCRIPT_ID')
            key = script['script_id']
            if key in self._scripts:
                raise PlanningError('DUPLICATE_SCRIPT_ID')
            self._scripts[key] = deepcopy(script)
        self._check_script = check_script
        self.priorities = priorities or {'safe_fallback': 100, 'comment_reply': 60, 'product_intro': 20}
        self._issued: dict[str, SpeechTurn] = {}

    @classmethod
    def from_file(cls, path: str | Path, **kwargs):
        """Đọc thư viện script JSON UTF-8; không thay đổi trạng thái phê duyệt."""
        return cls(json.loads(Path(path).read_text(encoding='utf-8')), **kwargs)

    def _issue(self, *, run_id, speech_type, text, sku_id, response_id, script_ref):
        """Tạo turn qua public contract và lưu bản phát hành để admission đối chiếu."""
        turn = SpeechTurn(speech_turn_id='TURN-' + uuid4().hex, run_id=run_id,
            speech_type=speech_type, text=text, sku_id=sku_id, response_id=response_id,
            script_ref=script_ref, priority=self.priorities[speech_type],
            created_at=datetime.now(timezone.utc))
        self._issued[turn.speech_turn_id] = turn
        return turn

    def _approved_script(self, script_id: str, speech_type: str, active_sku_id: str | None):
        """
        Kiểm tra ID, loại, nội dung, approval và phạm vi SKU của script.

        ``approved_at`` phải có múi giờ và ``approved_by`` không được rỗng.
        Đây là kiểm tra dữ liệu phê duyệt, không xác thực danh tính người duyệt.
        Các điều kiện được viết tự do phải do callback bên ngoài kiểm tra.
        """
        script = self._scripts.get(script_id)
        if script is None:
            raise PlanningError('SCRIPT_NOT_FOUND')
        approval = script.get('approval')
        if not isinstance(approval, dict) or approval.get('status') != 'approved' or not approval.get('approved_by') or not approval.get('approved_at'):
            raise PlanningError('SCRIPT_NOT_APPROVED')
        try:
            approved_at = datetime.fromisoformat(approval['approved_at'].replace('Z', '+00:00'))
            if not isinstance(approval['approved_by'], str) or not approval['approved_by'].strip() or approved_at.utcoffset() is None:
                raise ValueError('Invalid approval')
        except (ValueError, TypeError, AttributeError):
            raise PlanningError('INVALID_APPROVAL') from None
        if script.get('speech_type') != speech_type or not isinstance(script.get('text'), str) or not script['text'].strip():
            raise PlanningError('INVALID_SCRIPT')
        if speech_type == 'product_intro' and (not active_sku_id or script.get('sku_id') != active_sku_id):
            raise PlanningError('ACTIVE_SKU_MISMATCH')
        if speech_type == 'safe_fallback' and script.get('sku_id') is not None and script.get('sku_id') != active_sku_id:
            raise PlanningError('ACTIVE_SKU_MISMATCH')
        # Điều kiện sử dụng và evidence cần được kiểm tra tường minh từ bên ngoài.
        if (script.get('use_when') or script.get('evidence_refs')) and (self._check_script is None or self._check_script(deepcopy(script)) is not True):
            raise PlanningError('SCRIPT_CONDITIONS_NOT_VERIFIED')
        return script

    def from_response(self, response: AgentResponse, *, run_id: str, fallback_script_id: str | None = None,
                      active_sku_id: str | None = None) -> SpeechTurn:
        """
        Đổi AgentResponse thành lượt nói và giữ liên kết response_id/run_id.

        Answered và clarification_needed dùng nguyên answer_text làm reply.
        Blocked chỉ dùng nội dung safe_fallback đã duyệt; nếu không có script
        hợp lệ, hàm báo PlanningError và không tạo lượt để phát.
        """
        response = AgentResponse.model_validate(response.model_dump())
        if response.run_id != run_id:
            raise PlanningError('RUN_MISMATCH')
        if response.status == 'blocked':
            if not fallback_script_id:
                raise PlanningError('NO_APPROVED_FALLBACK')
            script = self._approved_script(fallback_script_id, 'safe_fallback', active_sku_id)
            return self._issue(run_id=run_id, speech_type='safe_fallback', text=script['text'],
                               sku_id=script.get('sku_id'), response_id=response.response_id, script_ref=fallback_script_id)
        return self._issue(run_id=run_id, speech_type='comment_reply', text=response.answer_text,
                           sku_id=response.resolved_sku_id, response_id=response.response_id, script_ref=None)

    def product_intro(self, script_id: str, *, run_id: str, active_sku_id: str) -> SpeechTurn:
        """Tạo lời giới thiệu từ script đúng active SKU, không cần AgentResponse."""
        script = self._approved_script(script_id, 'product_intro', active_sku_id)
        return self._issue(run_id=run_id, speech_type='product_intro', text=script['text'],
                           sku_id=script['sku_id'], response_id=None, script_ref=script_id)

    def is_issued(self, turn: SpeechTurn) -> bool:
        """Đối chiếu cả nội dung turn với bản do planner này phát hành."""
        return self._issued.get(turn.speech_turn_id) == turn


# ============================================================
# 2. ADMISSION - KIỂM TRA LƯỢT TRƯỚC KHI TỔNG HỢP
# ============================================================

@dataclass(frozen=True)
class AdmissionDecision:
    """Quyết định nội bộ cho một đầu vào; turn là None nếu dữ liệu sai schema."""
    turn: SpeechTurn | None
    accepted: bool
    reason: str


class SpeechAdmission:
    """
    Kiểm tra turn trước TTS và theo dõi các lượt đã được chấp nhận.

    Trạng thái seen/accepted chỉ nằm trong instance hiện tại. Thứ tự ưu tiên là
    safe_fallback, comment_reply, product_intro; cùng loại sắp theo priority
    giảm dần và giữ thứ tự đầu vào nếu priority bằng nhau.
    """
    def __init__(self, planner: SpeechPlanner):
        self.planner = planner
        self._seen: set[str] = set()
        self._accepted: dict[str, SpeechTurn] = {}

    def admit(self, turns, *, run_id: str, active_sku_id: str, now: datetime | None = None,
              deadlines: dict[str, datetime] | None = None) -> list[AdmissionDecision]:
        """
        Kiểm tra schema, nguồn planner, ID, run, active SKU và deadline nếu có.

        Caller phải cung cấp ``now`` và deadline có múi giờ khi áp dụng hạn.
        Không tự suy ra thời điểm hết hạn từ đồng hồ hệ thống hay timeline video.
        Kết quả gồm cả lượt được chấp nhận và lượt bị từ chối kèm reason.
        """
        if now is not None and (now.tzinfo is None or now.utcoffset() is None):
            raise ValueError('now must be timezone-aware')
        decisions = []
        for value in turns:
            try:
                turn = SpeechTurn.model_validate(value.model_dump() if isinstance(value, SpeechTurn) else value)
            except Exception:
                decisions.append(AdmissionDecision(None, False, 'INVALID_TURN'))
                continue
            reason = None
            if turn.speech_turn_id in self._seen:
                reason = 'DUPLICATE_TURN'
            elif not self.planner.is_issued(turn):
                reason = 'UNTRUSTED_SOURCE'
            elif turn.run_id != run_id:
                reason = 'RUN_MISMATCH'
            elif turn.speech_type == 'product_intro' and turn.sku_id != active_sku_id:
                reason = 'ACTIVE_SKU_MISMATCH'
            elif deadlines and turn.speech_turn_id in deadlines:
                deadline = deadlines[turn.speech_turn_id]
                if now is None or deadline.tzinfo is None or deadline.utcoffset() is None:
                    reason = 'INVALID_DEADLINE'
                elif now >= deadline:
                    reason = 'EXPIRED'
            if reason is None:
                self._seen.add(turn.speech_turn_id)
                self._accepted[turn.speech_turn_id] = turn
            decisions.append(AdmissionDecision(turn, reason is None, reason or 'ACCEPTED'))
        # Python sort ổn định: các lượt cùng nhóm và priority giữ thứ tự đầu vào.
        rank = {'safe_fallback': 0, 'comment_reply': 1, 'product_intro': 2}
        return sorted(decisions, key=lambda d: (not d.accepted, rank[d.turn.speech_type] if d.accepted else 0, -d.turn.priority if d.accepted else 0))

    def consume(self, turn: SpeechTurn) -> None:
        """
        Tiêu thụ quyền tổng hợp một lần cho turn đã admit và đúng nội dung.

        Quyền được tiêu thụ trước khi provider chạy; nếu TTS lỗi, caller cần
        chủ động tạo và admit lượt mới, không thể dùng lại quyền cũ.
        """
        if self._accepted.get(turn.speech_turn_id) != turn:
            raise PlanningError('TURN_NOT_ADMITTED')
        del self._accepted[turn.speech_turn_id]
