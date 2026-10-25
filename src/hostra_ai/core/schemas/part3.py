
"""Data Contracts Part 3 - HOSTRA AI PoC.

Bao gồm:
    RunManifest
    TimelineEvent
    AuditRecord

Schema chịu trách nhiệm:
    - Kiểm tra cấu trúc và kiểu dữ liệu.
    - Kiểm tra invariant trong MỘT bản ghi.
    - Chuẩn hóa timestamp UTC.
    - Bảo vệ cú pháp đường dẫn media.

Service/Integration chịu trách nhiệm:
    - Kiểm tra sự tồn tại và nội dung media.
    - Kiểm tra license, consent.
    - Đối chiếu CommentEvent, SpeechTurn, VideoArtifact.
    - Chuyển đổi offset_ms thành frame.
    - Kiểm tra thứ tự, overlap và video duration.
    - Điều phối Operator và thực hiện compositing.
"""

import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .common import ID_PATTERN


# ============================================================
# 1. TYPE DEFINITIONS
# ============================================================

# PoC chưa triển khai livestream realtime.
ExecutionMode = Literal["pre_rendered", "mock"]

# clip: ghép video lip-sync.
# pause: khoảng nghỉ không phát clip.
TimelineEventType = Literal["clip", "pause"]

# Kết quả của một hoạt động được ghi audit.
AuditOutcome = Literal["succeeded", "failed", "blocked"]


# Cấu hình chung cho ID:
# - Bắt buộc là string.
# - Không rỗng.
# - Tối đa 64 ký tự.
# - Tuân theo ID_PATTERN từ common.py.
_ID = {
    "strict": True,
    "min_length": 1,
    "max_length": 64,
    "pattern": ID_PATTERN,
}

_REASON_PATTERN = r"^[A-Z][A-Z0-9_]*$"


# ============================================================
# 2. INTERNAL HELPERS
# ============================================================

def _check_posix_media_path(
    value: str,
    *,
    error_code: str,
) -> list[str]:
    """Kiểm tra cú pháp đường dẫn media tương đối.

    Từ chối:
        - Đường dẫn tuyệt đối.
        - Windows backslash.
        - Dấu hai chấm.
        - Ký tự điều khiển ASCII và DEL.
        - Path traversal.
        - Thành phần '.' hoặc '..'.
        - Double slash.
        - Khoảng trắng thừa.

    Không kiểm tra file tồn tại hoặc đọc ổ đĩa.
    """

    if (
        not value
        or value != value.strip()
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(
            ord(ch) < 32 or ord(ch) == 127
            for ch in value
        )
    ):
        raise ValueError(error_code)

    parts = value.split("/")

    if any(
        part in ("", ".", "..")
        for part in parts
    ):
        raise ValueError(error_code)

    # Từ chối đường dẫn không canonical.
    if PurePosixPath(value).as_posix() != value:
        raise ValueError(error_code)

    return parts


def _utc(value: datetime) -> datetime:
    """Chuẩn hóa datetime có timezone về UTC.

    Pydantic AwareDatetime đã kiểm tra timezone
    trước khi hàm này được gọi.
    """
    return value.astimezone(timezone.utc)


# ============================================================
# 3. RUN MANIFEST
# ============================================================

class RunManifest(BaseModel):
    """Snapshot cấu hình của một phiên HOSTRA AI Demo.

    RunManifest mô tả:
        - Run ID.
        - Video nền.
        - Thông số kỹ thuật.
        - SKU và avatar.
        - Giấy phép được tham chiếu.
        - Chế độ thực thi.
        - Đường dẫn video đầu ra.
        - Mốc UTC tương ứng timeline offset_ms = 0.

    Phân biệt hai timestamp:

    timeline_start_at:
        Mốc thời gian gốc của kịch bản video.

    created_at:
        Thời điểm tạo bản ghi RunManifest.

    Hai thời điểm này không bắt buộc trùng nhau.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # -------------------------
    # A. Định danh
    # -------------------------

    run_id: str = Field(..., **_ID)

    # -------------------------
    # B. Video nền
    # -------------------------

    base_video_path: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=255,
    )

    # Giới hạn một run PoC tối đa 60 phút.
    base_duration_ms: int = Field(
        ...,
        strict=True,
        ge=1,
        le=3_600_000,
    )

    fps: float = Field(
        ...,
        strict=True,
        gt=0,
        le=120,
        allow_inf_nan=False,
    )

    width_px: int = Field(
        ...,
        strict=True,
        ge=64,
        le=4096,
    )

    height_px: int = Field(
        ...,
        strict=True,
        ge=64,
        le=4096,
    )

    # -------------------------
    # C. Cấu hình phiên
    # -------------------------

    active_sku_id: str = Field(..., **_ID)

    avatar_id: str = Field(..., **_ID)

    license_ref: str = Field(..., **_ID)

    execution_mode: ExecutionMode

    # -------------------------
    # D. Video đầu ra
    # -------------------------

    output_video_path: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=255,
    )

    # -------------------------
    # E. Timestamp
    # -------------------------

    # MỚI:
    # Mốc UTC tương ứng frame 0 / offset_ms = 0.
    timeline_start_at: AwareDatetime

    # Thời điểm tạo bản ghi.
    created_at: AwareDatetime

    # -------------------------
    # F. Validators
    # -------------------------

    @field_validator(
        "timeline_start_at",
        "created_at",
    )
    @classmethod
    def normalize_timestamps(
        cls,
        value: datetime,
    ) -> datetime:
        """Chuẩn hóa cả hai timestamp về UTC."""
        return _utc(value)

    @model_validator(mode="after")
    def validate_media_locations(self) -> "RunManifest":
        """Kiểm tra đường dẫn video nguồn và đầu ra."""

        # Video nền phải nằm trực tiếp trong:
        # shared_data/inputs/<file_id>.mp4

        source = _check_posix_media_path(
            self.base_video_path,
            error_code="INVALID_BASE_VIDEO_PATH",
        )

        if (
            len(source) != 3
            or source[:2] != ["shared_data", "inputs"]
        ):
            raise ValueError(
                "INVALID_BASE_VIDEO_PATH"
            )

        filename = source[2]

        if not filename.endswith(".mp4"):
            raise ValueError(
                "INVALID_BASE_VIDEO_PATH"
            )

        stem = filename[:-4]

        if (
            len(stem) > 64
            or re.fullmatch(ID_PATTERN, stem) is None
        ):
            raise ValueError(
                "INVALID_BASE_VIDEO_PATH"
            )

        # Video cuối cùng phải thuộc đúng run.
        destination = _check_posix_media_path(
            self.output_video_path,
            error_code="INVALID_FINAL_VIDEO_PATH",
        )

        expected = [
            "shared_data",
            "runs",
            self.run_id,
            "step3_final",
            "hostra_demo.mp4",
        ]

        if destination != expected:
            raise ValueError(
                "FINAL_VIDEO_OUTSIDE_RUN_DIRECTORY"
            )

        # Không kiểm tra timeline_start_at >= created_at.
        #
        # Lý do:
        # Trong mock demo, kịch bản bình luận có thể xảy ra
        # trước thời điểm hệ thống tạo manifest.

        return self


# ============================================================
# 4. TIMELINE EVENT
# ============================================================

class TimelineEvent(BaseModel):
    """Sự kiện media trên timeline demo.

    Mỗi event có hai khoảng thời gian tương ứng:

        [start_ms, end_ms)

        [start_frame, end_frame)

    Trong đó end_ms và end_frame đều exclusive.

    FrameMapper tính frame index một lần duy nhất.
    TimelineValidator kiểm tra kết quả với RunManifest.

    Hai event type:
        clip
        pause

    Không nhúng trạng thái Teleprompter vào schema này.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # -------------------------
    # A. Định danh
    # -------------------------

    event_id: str = Field(..., **_ID)

    run_id: str = Field(..., **_ID)

    event_type: TimelineEventType

    # -------------------------
    # B. Timeline tính bằng ms
    # -------------------------

    start_ms: int = Field(
        ...,
        strict=True,
        ge=0,
    )

    end_ms: int = Field(
        ...,
        strict=True,
        ge=1,
    )

    # -------------------------
    # C. Timeline tính bằng frame
    # -------------------------

    # MỚI:
    # Hai giá trị này do FrameMapper tạo ra.
    # Không được để mỗi module tự quy đổi.

    start_frame: int = Field(
        ...,
        strict=True,
        ge=0,
    )

    end_frame: int = Field(
        ...,
        strict=True,
        ge=1,
    )

    # -------------------------
    # D. Liên kết dữ liệu
    # -------------------------

    # Nullable nhưng bắt buộc gửi key.
    comment_id: str | None = Field(..., **_ID)

    speech_turn_id: str | None = Field(..., **_ID)

    audio_id: str | None = Field(..., **_ID)

    video_id: str | None = Field(..., **_ID)

    sku_id: str | None = Field(..., **_ID)

    created_at: AwareDatetime

    # -------------------------
    # E. Validators
    # -------------------------

    @field_validator("created_at")
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime,
    ) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def validate_event_consistency(self) -> "TimelineEvent":
        """Kiểm tra invariant của một event."""

        # Khoảng thời gian phải có độ dài dương.
        if self.end_ms <= self.start_ms:
            raise ValueError(
                "INVALID_TIMELINE_RANGE"
            )

        # Khoảng frame phải chứa ít nhất một frame.
        if self.end_frame <= self.start_frame:
            raise ValueError(
                "INVALID_FRAME_RANGE"
            )

        if self.event_type == "clip":

            # Clip phải tham chiếu đầy đủ:
            # SpeechTurn -> AudioArtifact -> VideoArtifact.
            #
            # comment_id có thể null cho lời dẫn chủ động.
            # sku_id có thể null khi không gắn SKU cụ thể.

            if not all((
                self.speech_turn_id,
                self.audio_id,
                self.video_id,
            )):
                raise ValueError(
                    "CLIP_REQUIRES_MEDIA_REFERENCES"
                )

        else:
            # pause không mang tham chiếu media/SKU.

            if any((
                self.comment_id,
                self.speech_turn_id,
                self.audio_id,
                self.video_id,
                self.sku_id,
            )):
                raise ValueError(
                    "PAUSE_FORBIDS_MEDIA_REFERENCES"
                )

        # KHÔNG kiểm tra công thức ms -> frame tại đây.
        #
        # Lý do:
        # Cần RunManifest.fps để kiểm tra, mà schema này
        # không được phép tự truy vấn manifest.
        #
        # TimelineValidator sẽ thực hiện đối chiếu.

        return self


# ============================================================
# 5. AUDIT RECORD
# ============================================================

class AuditRecord(BaseModel):
    """Bản ghi audit của một hoạt động trong HOSTRA AI.

    Cho phép:
        - Truy vết qua correlation_id.
        - Xác định module/action.
        - Ghi kết quả và mã nguyên nhân.

    Không lưu trực tiếp:
        - API keys.
        - Access tokens.
        - Raw prompts chứa dữ liệu nhạy cảm.
        - Thông tin cá nhân không cần thiết.

    Các sự kiện Operator giả lập và xác nhận thật
    phải được phân biệt ở tầng Service.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # -------------------------
    # A. Truy vết
    # -------------------------

    audit_id: str = Field(..., **_ID)

    run_id: str = Field(..., **_ID)

    correlation_id: str = Field(..., **_ID)

    # -------------------------
    # B. Hoạt động
    # -------------------------

    module: str = Field(..., **_ID)

    action: str = Field(..., **_ID)

    entity_type: str = Field(..., **_ID)

    entity_id: str = Field(..., **_ID)

    # -------------------------
    # C. Kết quả
    # -------------------------

    outcome: AuditOutcome

    reason_code: str | None = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=64,
        pattern=_REASON_PATTERN,
    )

    created_at: AwareDatetime

    # -------------------------
    # D. Validators
    # -------------------------

    @field_validator("created_at")
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime,
    ) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def validate_outcome_consistency(self) -> "AuditRecord":
        """Kiểm tra outcome và reason_code."""

        if (
            self.outcome == "succeeded"
            and self.reason_code is not None
        ):
            raise ValueError(
                "SUCCESS_FORBIDS_REASON_CODE"
            )

        if (
            self.outcome in ("failed", "blocked")
            and self.reason_code is None
        ):
            raise ValueError(
                "FAILURE_REQUIRES_REASON_CODE"
            )

        return self
