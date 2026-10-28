"""Đọc và kiểm tra cấu hình xử lý bình luận, tách khỏi logic nghiệp vụ."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CommentPolicy:
    """Các giá trị policy cần thiết cho triage và queue trong một lần chạy."""
    version: str
    duplicate_seconds: int
    deferred_seconds: int
    max_queue_size: int
    max_consecutive_per_viewer: int
    scores: dict[str, int]


def load_policy(path: str | Path) -> CommentPolicy:
    """Đọc YAML và từ chối các giá trị thiếu hoặc chính sách chưa được hỗ trợ."""
    with Path(path).open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    try:
        duplicate = data["duplicate"]
        deferred = data["deferred"]
        # Thuật toán hiện hỗ trợ đúng các lựa chọn này; không âm thầm bỏ qua config khác.
        if (duplicate["scope"] != "same_viewer_same_run" or
            duplicate["normalize_whitespace"] is not True or
            duplicate["case_insensitive"] is not True or
            duplicate["preserve_vietnamese_accents"] is not True or
            deferred["timeout_origin"] != "comment_received_at"):
            raise ValueError("unsupported duplicate or deferred policy")
        scores = data["scoring"]
        keys = {"base", "price", "technical", "comparison", "advice", "purchase", "follow_up"}
        # Mỗi nhóm điểm phải có trọng số nguyên không âm, kể cả điểm cơ sở.
        if not isinstance(scores, dict) or set(scores) != keys or any(type(v) is not int or v < 0 for v in scores.values()):
            raise ValueError("invalid scoring weights")
        values = (duplicate["window_seconds"], deferred["timeout_seconds"], data["queue"]["max_size"], data["queue"]["max_consecutive_per_viewer"])
        if any(type(v) is not int or v <= 0 for v in values):
            raise ValueError("timeouts and queue limits must be positive integers")
        version = data["policy_version"]
        if not isinstance(version, str) or not version:
            raise ValueError("invalid policy_version")
        return CommentPolicy(version, *values, dict(scores))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid comment policy {path}: {exc}") from exc
