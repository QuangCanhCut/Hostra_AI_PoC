"""Run HOSTRA Part 1 (M01->M05) then voice verified outputs with OpenAI TTS.

Copy to <repo>/scripts/preview_part1_rag_tts.py and run from the repo root.
This is a local *audition* utility: WAVs go to shared_data/tts_previews,
not to the official run's AudioArtifact registry. It never rewrites answers,
forces approval, or treats an arbitrary text snippet as M03-verified.

dry-run: .\.venv\Scripts\python.exe scripts\script_part1\preview_part1_rag_tts.py --reply-comment-id CMT-001 --intro-comment-id CMT-007 --confirm-live
run-with-openAI: .\.venv\Scripts\python.exe scripts\script_part1\preview_part1_rag_tts.py --reply-comment-id CMT-001 --intro-comment-id CMT-007 --confirm-live
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.core.schemas.part1 import AgentResponse, SpeechTurn
from hostra_ai.part1_agent_tts.pipeline import Part1Pipeline
from hostra_ai.part1_agent_tts.speech_planner import PlanningError, SpeechAdmission, SpeechPlanner
from hostra_ai.part1_agent_tts.tts_provider import (
    OpenAITTSProvider, load_tts_config, normalize_wav, validate_wav
)


def json_list(path: Path, field: str | None = None) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and field:
        data = data.get(field)
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise ValueError(f"File không phải một danh sách JSON hợp lệ: {path}")
    return data


def verified_reply(run_dir: Path, run_id: str, comment_id: str) -> tuple[str, dict]:
    """Find an approved *M05-emitted* reply, cross-checking response + turn."""
    answers = [AgentResponse.model_validate(x) for x in json_list(run_dir / "answers.json", "answers")]
    turns = [SpeechTurn.model_validate(x) for x in json_list(run_dir / "speech_turns.json", "speech_turns")]
    candidates = [a for a in answers if a.comment_id == comment_id and a.run_id == run_id]
    if len(candidates) != 1:
        raise ValueError(f"Cần đúng một AgentResponse cho {comment_id}; tìm thấy {len(candidates)}")
    a = candidates[0]
    if a.status not in ("answered", "clarification_needed") or not a.answer_text:
        raise ValueError(f"{comment_id} có status={a.status}, không được phát nội dung này.")
    if a.status == "answered" and not a.evidence_refs:
        raise ValueError(f"{comment_id} answered nhưng không có evidence_refs.")
    matches = [t for t in turns if t.run_id == run_id and t.response_id == a.response_id and t.speech_type == "comment_reply"]
    if len(matches) != 1:
        raise ValueError(f"Không tìm được duy nhất SpeechTurn comment_reply cho response {a.response_id}.")
    t = matches[0]
    if t.text != a.answer_text or t.sku_id != a.resolved_sku_id:
        raise ValueError("SpeechTurn không khớp AgentResponse, ngừng trước khi gọi TTS.")
    return t.text, {"comment_id": comment_id, "response_id": a.response_id,
                    "speech_turn_id": t.speech_turn_id, "status": a.status,
                    "evidence_refs": list(a.evidence_refs), "speech_type": t.speech_type}


def intro_from_approved_script(script_id: str, *, run_id: str, active_sku: str,
                                confirm_conditions: bool) -> tuple[str, dict]:
    """Only use an actually approved product_intro with explicit condition review."""
    scripts_path = ROOT / "shared_data/inputs/approved_product_scripts.json"
    scripts = json.loads(scripts_path.read_text(encoding="utf-8"))
    catalog_path = ROOT / "shared_data/inputs/catalog_skus.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    known_skus = {p["sku_id"] for p in catalog.get("products", [])}

    def check_conditions(script: dict) -> bool:
        # Human confirmation is REQUIRED for free-text use_when. Never auto-true.
        if not confirm_conditions or not active_sku or script.get("sku_id") != active_sku:
            return False
        refs = script.get("evidence_refs") or []
        if not isinstance(refs, list) or not refs:
            return False
        # The quick preview supports catalog-only script evidence. FAQ/other
        # refs require dedicated review tooling; refuse rather than guess.
        return all(isinstance(ref, str) and ref.startswith("catalog:")
                   and ref.partition(":")[2] in known_skus for ref in refs)

    planner = SpeechPlanner(scripts, check_script=check_conditions)
    turn = planner.product_intro(script_id, run_id=run_id, active_sku_id=active_sku)
    admission = SpeechAdmission(planner)
    decisions = admission.admit([turn], run_id=run_id, active_sku_id=active_sku)
    if len(decisions) != 1 or not decisions[0].accepted:
        raise ValueError(f"Intro bị Admission từ chối: {[d.reason for d in decisions]}")
    return turn.text, {"script_ref": script_id, "speech_turn_id": turn.speech_turn_id,
                       "speech_type": "product_intro", "active_sku_id": active_sku}


def active_sku_from_comments(path: Path) -> str:
    events = json_list(path)
    if not events or not isinstance(events[0].get("active_sku_id"), str):
        raise ValueError("Không thể xác định active_sku_id từ comments input.")
    return events[0]["active_sku_id"]


def main() -> int:
    p = argparse.ArgumentParser(description="M01-M05 -> verified answers -> real OpenAI TTS preview")
    p.add_argument("--confirm-live", action="store_true", help="Cho phép TTS calls có tính phí")
    p.add_argument("--run-id", default=None, help="ID run mới (không dùng lại ID có sẵn)")
    p.add_argument("--comments", type=Path, default=ROOT / "shared_data/inputs/mock_comments.json")
    p.add_argument("--config", type=Path, default=ROOT / "configs/app.yaml")
    p.add_argument("--reply-comment-id", default="CMT-001")
    p.add_argument("--intro-script-id", default="SCRIPT-ASUS-001")
    p.add_argument("--intro-comment-id", default=None,
                   help="Dùng comment khác làm product highlight từ M03/RAG; KHÔNG phải product_intro đã duyệt")
    p.add_argument("--confirm-intro-conditions", action="store_true",
                   help="Xác nhận đã đối chiếu điều kiện use_when và evidence của script ĐÃ được duyệt")
    p.add_argument("--no-intro", action="store_true", help="Chỉ tạo reply.wav")
    p.add_argument("--voice", default=None)
    args = p.parse_args()
    if args.confirm_live and not os.getenv("OPENAI_API_KEY"):
        p.error("Thiếu OPENAI_API_KEY của terminal.")
    if args.intro_comment_id == args.reply_comment_id:
        p.error("--intro-comment-id phải khác --reply-comment-id.")

    run_id = args.run_id or "RUN-RAG-PREVIEW-" + uuid4().hex[:12]
    run_dir = ROOT / "shared_data/runs" / run_id / "step1_agent_audio"
    if (ROOT / "shared_data/runs" / run_id).exists():
        p.error("Run ID đã tồn tại; M05 không ghi đè. Chọn ID khác.")

    # Genuine M05 pipeline handles M01 triage, M02 retrieval, M03 verification,
    # M04 mock admission, and writes validated M05 JSON artifacts.
    print("[1/3] Chạy M01→M05 offline, truy xuất Catalog/RAG và tạo AgentResponse...")
    pipe = Part1Pipeline(project_root=ROOT, output_root=ROOT,
                         comments_path=args.comments, config_path=args.config,
                         service_interval_seconds=0)
    result = pipe.run(run_id)
    if result.get("status") != "completed":
        raise RuntimeError(f"M05 chưa hoàn tất: {result.get('status')}. Kiểm tra {run_dir}")
    if not (run_dir / "evaluation.json").exists():
        raise RuntimeError("M05 không có evaluation.json; không coi run là thành công.")

    print("[2/3] Chọn câu trả lời đã qua M03/M05 và kiểm tra liên kết...")
    reply, reply_meta = verified_reply(run_dir, run_id, args.reply_comment_id)
    clips = [("reply", reply, reply_meta)]

    if not args.no_intro and args.intro_comment_id:
        intro, intro_meta = verified_reply(run_dir, run_id, args.intro_comment_id)
        intro_meta["notice"] = "Đây là comment_reply do M03 tạo, KHÔNG phải product_intro."
        clips.insert(0, ("product_highlight_from_reply", intro, intro_meta))
    elif not args.no_intro:
        try:
            intro, intro_meta = intro_from_approved_script(
                args.intro_script_id, run_id=run_id,
                active_sku=active_sku_from_comments(args.comments),
                confirm_conditions=args.confirm_intro_conditions,
            )
            clips.insert(0, ("intro", intro, intro_meta))
        except (PlanningError, ValueError, KeyError) as exc:
            # Most likely pending_review (15 scripts). Do not bypass approval.
            print(f"[Không tạo intro] {type(exc).__name__}: {exc}")
            print("Intro chỉ phát được khi script đã được phê duyệt thật và điều kiện được xác nhận.")

    print("\n=== NỘI DUNG THỰC SỰ ĐƯỢC M05/M03 TẠO ===")
    for label, utterance, source in clips:
        print(f"[{label}] {source}\n{utterance}\n")
    if not args.confirm_live:
        print("DRY RUN: chưa gọi OpenAI. Để tạo WAV thật, chạy lại với run ID KHÁC và --confirm-live.")
        return 0

    config_original = load_tts_config(args.config)
    config = replace(config_original, provider="openai",
                     live_api_opt_in=True, voice=args.voice or config_original.voice)
    output = ROOT / "shared_data/tts_previews" / ("PREVIEW-RAG-" + uuid4().hex[:12])
    output.mkdir(parents=True, exist_ok=False)
    provider = OpenAITTSProvider()
    metadata = {"run_id": run_id, "mode": "RAG_M05_VERIFIED_RESPONSE_TO_REAL_TTS_PREVIEW",
                "voice": config.voice, "model": config.model,
                "note": "Preview riêng; không phải AudioArtifact chính thức của M05", "clips": []}
    print("[3/3] Gọi OpenAI TTS trên nội dung có nguồn thật từ pipeline...")
    for label, text, source in clips:
        raw = provider.synthesize(text, config)
        wav = normalize_wav(raw, config.sample_rate_hz)
        duration = validate_wav(wav, config.sample_rate_hz)
        (output / f"{label}.wav").write_bytes(wav)
        metadata["clips"].append({"file": label + ".wav", "text": text,
                                  "source": source, "duration_ms": duration})
        print(f"  {label}.wav: {duration} ms | nguồn: {source}")
    (output / "preview_info.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã tạo WAV ở: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LỖI: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
