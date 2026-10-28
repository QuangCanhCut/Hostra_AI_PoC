"""Regression cho lỗi tmp_path Windows, không chỉnh quyền Temp của người dùng."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
INGEST_TESTS = ROOT / "tests/unit/test_part1_code/test_comment_ingest.py"


@pytest.mark.skipif(os.name != "nt", reason="Thiết lập thư mục tạm riêng chỉ áp dụng Windows")
def test_windows_ignores_unusable_global_pytest_temp(tmp_path):
    # Trỏ thư mục Temp của pytest vào một file để mô phỏng vị trí không thể dùng.
    # Nếu thiếu hook mới, các test dùng tmp_path sẽ lỗi ngay trong bước setup.
    unusable_temp = tmp_path / "not-a-directory"
    unusable_temp.write_text("Không phải thư mục tạm", encoding="utf-8")
    environment = dict(os.environ, PYTEST_DEBUG_TEMPROOT=str(unusable_temp))
    result = subprocess.run([sys.executable, "-m", "pytest", str(INGEST_TESTS), "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "11 passed" in result.stdout
    assert unusable_temp.is_file()  # Không sửa hoặc xóa vị trí Temp bị lỗi.


def test_explicit_basetemp_is_honored(tmp_path):
    explicit_temp = tmp_path / "explicit-session"
    result = subprocess.run([sys.executable, "-m", "pytest", str(INGEST_TESTS), "-q", "-p", "no:cacheprovider",
                             "--basetemp", str(explicit_temp)], cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    # Người gọi sở hữu vòng đời của --basetemp; hook không tự dọn đường dẫn này.
    assert explicit_temp.is_dir()
