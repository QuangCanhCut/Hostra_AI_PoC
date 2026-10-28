"""Kiểm tra CLI mặc định không gọi API, kể cả môi trường thiếu .env/key."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


def run(script, *args, cwd=ROOT, as_module=False):
    environment = dict(os.environ)
    environment.pop("OPENAI_API_KEY", None)
    # Không để PYTHONPATH trong IDE che giấu lỗi import của CLI chạy độc lập.
    environment.pop("PYTHONPATH", None)
    command = ([sys.executable, "-m", f"scripts.script_rag.{Path(script).stem}"] if as_module
               else [sys.executable, str(ROOT / "scripts/script_rag" / script)])
    return subprocess.run([*command, *args],
        cwd=cwd, env=environment, text=True, encoding="utf-8", capture_output=True, check=False)


def test_default_build_and_lexical_cli():
    result = run("build_index.py", "--index-path", "does-not-exist/index.json")
    assert result.returncode == 0 and "DRY RUN" in result.stdout
    result = run("search_faq.py", "ASUS RAM", "--mode", "lexical")
    assert result.returncode == 0 and "FAQ-ASUS-004" in result.stdout
    result = run("search_faq.py", "RAM", "--mode", "semantic", "--index-path", "missing/index.json")
    assert result.returncode == 1 and "ERROR" in result.stdout


def test_evaluation_cli_offline(tmp_path):
    path = tmp_path / "report.json"
    result = run("evaluate_rag.py", "--output", str(path))
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(path.read_text(encoding="utf-8"))
    assert len(report["reports"]) == 1 and report["reports"][0]["mode"] == "lexical"
    metrics = report["reports"][0]["metrics"]
    assert all(0 <= value <= 1 for value in metrics.values())
    assert "NOT RUN" in result.stdout


def test_only_ood_dataset_has_no_recall_denominator(tmp_path):
    dataset = tmp_path / "ood.json"
    dataset.write_text(json.dumps([{"query_id": "ood", "query": "bóng đá", "relevant_faq_ids": [],
                                  "expected_status": "no_hit"}]), encoding="utf-8")
    result = run("evaluate_rag.py", "--dataset", str(dataset))
    assert result.returncode == 0 and "N/A" in result.stdout
    assert run("build_index.py", "--smoke").returncode == 1


@pytest.mark.parametrize("script", ["build_index.py", "search_faq.py", "evaluate_rag.py"])
@pytest.mark.parametrize("as_module", [False, True], ids=["direct_file", "module"])
def test_cli_imports_without_pythonpath(tmp_path, script, as_module):
    # File trực tiếp phải chạy cả ngoài root; -m cần cwd chứa namespace scripts.
    result = run(script, "--help", cwd=ROOT if as_module else tmp_path, as_module=as_module)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--allow-api" in result.stdout
