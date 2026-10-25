"""Các hằng số và hàm kiểm tra dùng chung cho data contract của HOSTRA AI."""

from datetime import datetime, timezone
from pathlib import PurePosixPath


ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"


def normalize_utc(value: datetime) -> datetime:
    """Chuyển thời điểm đã có múi giờ về UTC."""
    return value.astimezone(timezone.utc)


def validate_relative_media_path(value: str, *, suffix: str) -> str:
    """Kiểm tra đường dẫn media POSIX tương đối mà không truy cập hệ thống file."""
    value = value.strip()
    path = PurePosixPath(value)

    if (
        not value
        or "\\" in value
        or ":" in value
        or any(ord(char) < 32 for char in value)
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") for part in value.split("/"))
        or path.suffix != suffix
    ):
        raise ValueError("INVALID_RELATIVE_MEDIA_PATH")

    return value