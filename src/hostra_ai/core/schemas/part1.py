
"""
HOSTRA AI PoC - Part 1 Data Contracts.

Schemas:
    1. CommentEvent
    2. AgentResponse
    3. AudioArtifact

These contracts are shared with other modules.
"""

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
# 1. COMMENT EVENT V1
# ============================================================

class CommentEvent(BaseModel):
    """
    Normalized comment event for HOSTRA AI PoC.

    Every comment from mock or web must follow this contract.
    The backend attaches the Active SKU before creating it.
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
# 2. AGENT RESPONSE V1
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
    Final validated output of the HOSTRA AI Agent.

    This model must only contain results after Agent processing
    and verification.

    It must not represent raw, unverified LLM output.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # Identifiers
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
    # Product resolution
    # --------------------------------------------------------

    resolved_sku_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # Agent processing outcome
    # --------------------------------------------------------

    status: Literal[
        "answered",
        "clarification_needed",
        "blocked",
    ]

    # --------------------------------------------------------
    # Final response text
    # --------------------------------------------------------

    answer_text: str | None = Field(
        ...,
        min_length=1,
        max_length=500,
        strict=True,
    )

    # --------------------------------------------------------
    # Verification evidence
    # --------------------------------------------------------

    evidence_refs: tuple[str, ...] = Field(
        ...,
        max_length=10,
    )

    # --------------------------------------------------------
    # Processing reason
    # --------------------------------------------------------

    reason_code: AgentReasonCode | None

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    created_at: AwareDatetime

    # --------------------------------------------------------
    # Field validators
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
            if not ref or len(ref) > 128:
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
    # Cross-field validator
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_status_consistency(self):

        # CASE 1: Answered
        if self.status == "answered":

            if self.answer_text is None:
                raise ValueError(
                    "ANSWER_TEXT_REQUIRED"
                )

            if self.reason_code is not None:
                raise ValueError(
                    "REASON_CODE_MUST_BE_NULL"
                )

            # Product-specific answers require evidence.
            if (
                self.resolved_sku_id is not None
                and not self.evidence_refs
            ):
                raise ValueError(
                    "EVIDENCE_REQUIRED"
                )

        # CASE 2: Clarification needed
        elif self.status == "clarification_needed":

            if self.answer_text is None:
                raise ValueError(
                    "CLARIFICATION_TEXT_REQUIRED"
                )

            if self.reason_code not in CLARIFICATION_REASONS:
                raise ValueError(
                    "INVALID_CLARIFICATION_REASON"
                )

        # CASE 3: Blocked
        elif self.status == "blocked":

            if self.answer_text is not None:
                raise ValueError(
                    "BLOCKED_RESPONSE_CANNOT_HAVE_TEXT"
                )

            if self.reason_code not in BLOCK_REASONS:
                raise ValueError(
                    "INVALID_BLOCK_REASON"
                )

        return self


# ============================================================
# 3. AUDIO ARTIFACT V1
# ============================================================

class AudioArtifact(BaseModel):
    """
    Metadata for successfully generated TTS audio.

    The TTS service creates this artifact only after
    audio generation and file validation succeed.

    Blocked AgentResponses must not produce AudioArtifacts.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # Identifiers
    # --------------------------------------------------------

    audio_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    response_id: str = Field(
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
    # Audio file location
    # --------------------------------------------------------

    file_path: str = Field(
        min_length=1,
        max_length=255,
        strict=True,
    )

    # --------------------------------------------------------
    # Audio technical metadata
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
    # Timestamp
    # --------------------------------------------------------

    created_at: AwareDatetime

    # --------------------------------------------------------
    # Field validators
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
            or any(ord(ch) < 32 for ch in value)
            or path.is_absolute()
            or path.as_posix() != value
            or any(
                part in ("", ".", "..")
                for part in value.split("/")
            )
            or path.suffix != ".wav"
        ):
            raise ValueError(
                "file_path must be a safe relative .wav path"
            )

        return value

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)
