"""Public contracts shared by HOSTRA AI PoC modules."""

# ============================================================
# 1. CÁC HẰNG SỐ DÙNG CHUNG
# ============================================================

from .common import ID_PATTERN


# ============================================================
# 2. DATA CONTRACTS PART 1
# ============================================================

from .part1 import (
    AgentReasonCode,
    AgentResponse,
    AudioArtifact,
    BLOCK_REASONS,
    CLARIFICATION_REASONS,
    CommentDecision,
    CommentEvent,
    SpeechTurn,
    SpeechType,
    TRIAGE_REASONS_BY_ACTION,
    TriageAction,
    TriageReasonCode,
)


# ============================================================
# 3. DATA CONTRACTS PART 2
# ============================================================

from .part2 import (
    RenderJob,
    RenderStatus,
    VideoArtifact,
)


# ============================================================
# 4. DATA CONTRACTS PART 3
# ============================================================

# Public exports - Part 3
from .part3 import (
    RunManifest,
    TimelineEvent,
    AuditRecord,
)



# ============================================================
# 5. PUBLIC EXPORTS
# ============================================================

# Danh sách các thành phần có thể import công khai từ:
#
# from hostra_ai.core.schemas import ...
#
# Không cần import trực tiếp từ part1.py hoặc part2.py.

__all__ = [
    # Common
    "ID_PATTERN",

    # Part 1
    "AgentReasonCode",
    "AgentResponse",
    "AudioArtifact",
    "BLOCK_REASONS",
    "CLARIFICATION_REASONS",
    "CommentDecision",
    "CommentEvent",
    "SpeechTurn",
    "SpeechType",
    "TRIAGE_REASONS_BY_ACTION",
    "TriageAction",
    "TriageReasonCode",

    # Part 2
    "RenderJob",
    "RenderStatus",
    "VideoArtifact",

    # Part 3
    "RunManifest",
    "TimelineEvent",
    "AuditRecord",
]