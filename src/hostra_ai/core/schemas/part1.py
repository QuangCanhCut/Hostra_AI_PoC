"""
HOSTRA AI PoC - Hợp đồng dữ liệu Part 1.

Các schema:
    1. CommentEvent
    2. CommentDecision
    3. AgentResponse
    4. SpeechTurn
    5. AudioArtifact

Chỉ kiểm tra cấu trúc và tính nhất quán nội bộ.
Lọc bình luận, xếp hàng, đối chiếu ID và kiểm tra file thuộc service.
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
# 1. COMMENT EVENT - BÌNH LUẬN ĐẦU VÀO
# ============================================================

class CommentEvent(BaseModel):
    """
    Bình luận đã được chuẩn hóa trong HOSTRA AI PoC.

    Bình luận từ mock hoặc web đều phải tuân theo hợp đồng này.
    Backend gắn Active SKU trước khi tạo CommentEvent.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    comment_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    viewer_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    source: Literal["mock", "web"]

    text: str = Field(
        min_length=1,
        max_length=1000,
        strict=True,
    )

    active_sku_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    received_at: AwareDatetime

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("received_at")
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)


# ============================================================
# 2. COMMENT DECISION - KẾT QUẢ PHÂN LOẠI BÌNH LUẬN
# ============================================================

TriageAction = Literal[
    "selected",
    "deferred",
    "skipped",
    "escalated",
]

TriageReasonCode = Literal[
    "LOW_PRIORITY",
    "QUEUE_BUSY",
    "RATE_LIMITED",
    "SPAM",
    "DUPLICATE",
    "OFF_TOPIC",
    "EXPIRED",
    "HUMAN_REQUIRED",
]

TRIAGE_REASONS_BY_ACTION = {
    "selected": frozenset(),
    "deferred": frozenset({"LOW_PRIORITY", "QUEUE_BUSY", "RATE_LIMITED"}),
    "skipped": frozenset({"SPAM", "DUPLICATE", "OFF_TOPIC", "EXPIRED"}),
    "escalated": frozenset({"HUMAN_REQUIRED"}),
}


class CommentDecision(BaseModel):
    """
    Một kết quả đánh giá bình luận bởi Comment Triage.

    Bình luận deferred có thể được đánh giá lại, tạo quyết định mới
    với decision_id khác. Service chịu trách nhiệm timeout, kiểm tra
    trùng lặp và không gọi Agent nhiều lần cho cùng bình luận.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    decision_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    comment_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    action: TriageAction
    reason_code: TriageReasonCode | None = Field(...)
    priority_score: int = Field(strict=True, ge=0, le=100)
    duplicate_of: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    policy_version: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    decided_at: AwareDatetime

    @field_validator("decided_at")
    @classmethod
    def normalize_decided_at(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_decision(self):
        allowed_reasons = TRIAGE_REASONS_BY_ACTION[self.action]

        if self.action == "selected":
            if self.reason_code is not None:
                raise ValueError("SELECTED_REASON_MUST_BE_NULL")
        elif self.reason_code not in allowed_reasons:
            raise ValueError("INVALID_TRIAGE_REASON_FOR_ACTION")

        if self.reason_code == "DUPLICATE":
            if self.duplicate_of is None:
                raise ValueError("DUPLICATE_REFERENCE_REQUIRED")
            if self.duplicate_of == self.comment_id:
                raise ValueError("CANNOT_DUPLICATE_SELF")
        elif self.duplicate_of is not None:
            raise ValueError("DUPLICATE_REFERENCE_NOT_ALLOWED")

        return self


# ============================================================
# 3. AGENT RESPONSE - KẾT QUẢ XỬ LÝ CỦA AGENT
# ============================================================

AgentReasonCode = Literal[
    "REFERENCE_AMBIGUOUS",
    "DETAIL_MISSING",
    "PRODUCT_NOT_FOUND",
    "VERIFICATION_FAILED",
    "CATALOG_UNAVAILABLE",
    "UNSUPPORTED_REQUEST",
    "INTERNAL_ERROR",
]


CLARIFICATION_REASONS = frozenset({
    "REFERENCE_AMBIGUOUS",
    "DETAIL_MISSING",
    "PRODUCT_NOT_FOUND",
})


BLOCK_REASONS = frozenset({
    "VERIFICATION_FAILED",
    "CATALOG_UNAVAILABLE",
    "UNSUPPORTED_REQUEST",
    "INTERNAL_ERROR",
})


class AgentResponse(BaseModel):
    """
    Kết quả cuối cùng đã qua kiểm chứng của HOSTRA AI Agent.

    Model này chỉ chứa kết quả sau khi Agent xử lý
    và hệ thống kiểm chứng thông tin.

    Không dùng model này để lưu đầu ra LLM thô chưa kiểm chứng.
    Mọi response answered đều cần ít nhất một nguồn bằng chứng;
    service chịu trách nhiệm xác minh nội dung và nguồn tham chiếu.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # Các trường định danh
    # --------------------------------------------------------

    response_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    comment_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    viewer_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # Sản phẩm được xác định từ câu hỏi và ngữ cảnh
    # --------------------------------------------------------

    resolved_sku_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # Trạng thái xử lý của Agent
    # --------------------------------------------------------

    status: Literal[
        "answered",
        "clarification_needed",
        "blocked",
    ]

    # --------------------------------------------------------
    # Nội dung câu trả lời cuối cùng
    # --------------------------------------------------------

    answer_text: str | None = Field(
        ...,
        min_length=1,
        max_length=500,
        strict=True,
    )

    # --------------------------------------------------------
    # Tham chiếu bằng chứng dùng để kiểm chứng
    # --------------------------------------------------------

    evidence_refs: tuple[str, ...] = Field(
        ...,
        max_length=10,
    )

    # --------------------------------------------------------
    # Mã lý do xử lý
    # --------------------------------------------------------

    reason_code: AgentReasonCode | None

    # --------------------------------------------------------
    # Thời điểm tạo kết quả
    # --------------------------------------------------------

    created_at: AwareDatetime

    # --------------------------------------------------------
    # Kiểm tra và chuẩn hóa từng trường
    # --------------------------------------------------------

    @field_validator("answer_text", mode="before")
    @classmethod
    def normalize_answer_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(
        cls,
        refs: tuple[str, ...],
    ) -> tuple[str, ...]:

        normalized_refs = tuple(
            ref.strip() for ref in refs
        )

        for ref in normalized_refs:
            if (
                not ref
                or len(ref) > 128
                or any(ord(char) < 32 or ord(char) == 127 for char in ref)
            ):
                raise ValueError(
                    "INVALID_EVIDENCE_REFERENCE"
                )

        if len(normalized_refs) != len(set(normalized_refs)):
            raise ValueError(
                "DUPLICATE_EVIDENCE_REFERENCE"
            )

        return normalized_refs

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)

    # --------------------------------------------------------
    # Kiểm tra tính nhất quán giữa các trường
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_status_consistency(self):

        # TRƯỜNG HỢP 1: Agent trả lời thành công
        if self.status == "answered":

            if self.answer_text is None:
                raise ValueError(
                    "ANSWER_TEXT_REQUIRED"
                )

            if self.reason_code is not None:
                raise ValueError(
                    "REASON_CODE_MUST_BE_NULL"
                )

            # Kể cả chính sách chung không gắn SKU cũng phải có bằng chứng.
            if not self.evidence_refs:
                raise ValueError(
                    "EVIDENCE_REQUIRED"
                )

        # TRƯỜNG HỢP 2: Cần hỏi lại để làm rõ thông tin
        elif self.status == "clarification_needed":

            if self.answer_text is None:
                raise ValueError(
                    "CLARIFICATION_TEXT_REQUIRED"
                )

            if self.reason_code not in CLARIFICATION_REASONS:
                raise ValueError(
                    "INVALID_CLARIFICATION_REASON"
                )

        # TRƯỜNG HỢP 3: Câu trả lời bị chặn
        elif self.status == "blocked":

            if self.answer_text is not None:
                raise ValueError(
                    "BLOCKED_RESPONSE_CANNOT_HAVE_TEXT"
                )

            if self.reason_code not in BLOCK_REASONS:
                raise ValueError(
                    "INVALID_BLOCK_REASON"
                )

            # Evidence của kết quả bị chặn thuộc Verification/Audit Log,
            # không phải danh sách bằng chứng cho câu trả lời hợp lệ.
            if self.evidence_refs:
                raise ValueError("BLOCKED_RESPONSE_CANNOT_HAVE_EVIDENCE")

        return self


# ============================================================
# 4. SPEECH TURN - LƯỢT PHÁT NGÔN HỢP LỆ
# ============================================================

SpeechType = Literal[
    "product_intro",
    "comment_reply",
    "safe_fallback",
]


class SpeechTurn(BaseModel):
    """
    Một lượt nói hợp lệ để scheduler đưa vào hàng đợi TTS.

    Không dùng để lưu trạng thái đang phát hoặc logic xếp hàng.
    Service kiểm tra nội dung khớp nguồn và Active SKU trước khi phát.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    speech_turn_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    speech_type: SpeechType
    sku_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    text: str = Field(
        min_length=1,
        max_length=500,
        strict=True,
    )
    response_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )
    script_ref: str | None = Field(
        ...,
        min_length=1,
        max_length=128,
        strict=True,
    )
    priority: int = Field(strict=True, ge=0, le=100)
    created_at: AwareDatetime

    @field_validator("text", "script_ref", mode="before")
    @classmethod
    def normalize_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("script_ref")
    @classmethod
    def validate_script_ref(cls, value: str | None):
        if value is not None and any(
            ord(char) < 32 or ord(char) == 127 for char in value
        ):
            raise ValueError("INVALID_SCRIPT_REFERENCE")
        return value

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_origin(self):
        if self.speech_type == "comment_reply":
            if self.response_id is None or self.script_ref is not None:
                raise ValueError("COMMENT_REPLY_REQUIRES_AGENT_RESPONSE")
        elif self.speech_type == "product_intro":
            if self.response_id is not None or self.script_ref is None:
                raise ValueError("PRODUCT_INTRO_REQUIRES_SCRIPT")
            if self.sku_id is None:
                raise ValueError("PRODUCT_INTRO_REQUIRES_SKU")
        elif self.speech_type == "safe_fallback":
            # response_id có thể tham chiếu một AgentResponse blocked;
            # không có response_id khi fallback do lỗi hệ thống chung.
            if self.script_ref is None:
                raise ValueError("SAFE_FALLBACK_REQUIRES_SCRIPT")
        return self


# ============================================================
# 5. AUDIO ARTIFACT - THÔNG TIN FILE ÂM THANH
# ============================================================

class AudioArtifact(BaseModel):
    """
    Thông tin của file âm thanh TTS đã tạo thành công.

    TTS service chỉ tạo AudioArtifact sau khi sinh âm thanh
    và kiểm tra file thành công.

    Mọi audio thuộc một SpeechTurn; response_id có thể None đối với
    product_intro hoặc fallback hệ thống. Nếu safe_fallback liên quan
    AgentResponse blocked, response_id được dùng để truy vết.
    Không phát answer_text từ blocked response; chỉ được phát script
    fallback đã duyệt. Service kiểm tra liên kết và file WAV thực tế.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # Các trường định danh
    # --------------------------------------------------------

    audio_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    speech_turn_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    response_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    voice_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # Đường dẫn file âm thanh
    # --------------------------------------------------------

    file_path: str = Field(
        min_length=1,
        max_length=255,
        strict=True,
    )

    # --------------------------------------------------------
    # Thông số kỹ thuật của file âm thanh
    # --------------------------------------------------------

    format: Literal["wav"]

    codec: Literal["pcm_s16le"]

    sample_rate_hz: int = Field(
        strict=True,
        ge=8000,
        le=96000,
    )

    channels: Literal[1]

    duration_ms: int = Field(
        strict=True,
        gt=0,
    )

    # --------------------------------------------------------
    # Thời điểm tạo file âm thanh
    # --------------------------------------------------------

    created_at: AwareDatetime

    # --------------------------------------------------------
    # Kiểm tra và chuẩn hóa từng trường
    # --------------------------------------------------------

    @field_validator("file_path")
    @classmethod
    def validate_file_path(
        cls,
        value: str,
    ) -> str:

        value = value.strip()
        path = PurePosixPath(value)

        if (
            not value
            or "\\" in value
            or ":" in value
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
            or path.is_absolute()
            or path.as_posix() != value
            or any(
                part in ("", ".", "..")
                for part in value.split("/")
            )
            or path.suffix != ".wav"
            or re.fullmatch(ID_PATTERN, path.stem) is None
        ):
            raise ValueError("INVALID_AUDIO_FILE_PATH")

        return value

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_run_audio_directory(self):
        path_parts = PurePosixPath(self.file_path).parts
        expected_prefix = (
            "shared_data",
            "runs",
            self.run_id,
            "step1_agent_audio",
            "audio",
        )

        if len(path_parts) != 6 or path_parts[:5] != expected_prefix:
            raise ValueError("AUDIO_FILE_OUTSIDE_RUN_DIRECTORY")

        # Một file WAV mang tên <audio_id>.wav, nhất quán giữa các bước.
        if path_parts[-1] != f"{self.audio_id}.wav":
            raise ValueError("AUDIO_FILENAME_ID_MISMATCH")

        return self
