"""Contract test Part 1 -> Part 2 -> Part 3.

Kiểm tra:
- Public exports.
- JSON serialization/deserialization.
- Tên field của hai schema.
- Dữ liệu bàn giao cho Part 3.

Không kiểm tra file hoặc giấy phép thật.
Các kiểm tra liên bản ghi thuộc về service/integration test.
"""

import json
import unittest

from datetime import datetime, timedelta, timezone

import hostra_ai.core.schemas as public_schemas

from hostra_ai.core.schemas.part2 import (
    RenderJob,
    VideoArtifact,
)


# ============================================================
# 1. DỮ LIỆU MẪU
# ============================================================

NOW = datetime(
    2026, 10, 25,
    tzinfo=timezone.utc,
)


# ============================================================
# 2. CONTRACT TESTS
# ============================================================

class TestPart2Contract(unittest.TestCase):

    # --------------------------------------------------------
    # 2.1. PUBLIC EXPORTS
    # --------------------------------------------------------

    def test_public_exports(self):
        """Hai schema phải được export từ core.schemas."""

        self.assertIs(
            public_schemas.RenderJob,
            RenderJob,
        )

        self.assertIs(
            public_schemas.VideoArtifact,
            VideoArtifact,
        )

        self.assertIn(
            "RenderStatus",
            public_schemas.__all__,
        )

    # --------------------------------------------------------
    # 2.2. JSON ROUND-TRIP CỦA RENDER JOB
    # --------------------------------------------------------

    def test_queued_running_succeeded_snapshots_roundtrip(self):
        """Serialize và deserialize không được làm sai dữ liệu."""

        base = {
            "render_job_id": "job-01",
            "run_id": "run-01",
            "audio_id": "audio-01",
            "speech_turn_id": "turn-01",
            "source_video_path": (
                "shared_data/inputs/base_operator.mp4"
            ),
            "avatar_id": "avatar-01",
            "license_ref": "license-01",
            "created_at": NOW,
        }

        states = [
            # Trạng thái queued.
            {
                "status": "queued",
                "started_at": None,
                "finished_at": None,
                "output_video_id": None,
                "error_code": None,
            },

            # Trạng thái running.
            {
                "status": "running",
                "started_at": NOW,
                "finished_at": None,
                "output_video_id": None,
                "error_code": None,
            },

            # Trạng thái succeeded.
            {
                "status": "succeeded",
                "started_at": NOW,
                "finished_at": NOW + timedelta(seconds=3),
                "output_video_id": "vid-01",
                "error_code": None,
            },
        ]

        for data in states:
            with self.subTest(status=data["status"]):

                # Tạo RenderJob.
                obj = RenderJob(**base, **data)

                # Chuyển object thành JSON và khôi phục.
                restored = RenderJob.model_validate_json(
                    obj.model_dump_json()
                )

                # Nội dung phải được bảo toàn.
                self.assertEqual(restored, obj)

                self.assertEqual(
                    restored.run_id,
                    "run-01",
                )

                self.assertEqual(
                    restored.audio_id,
                    "audio-01",
                )

                self.assertEqual(
                    restored.speech_turn_id,
                    "turn-01",
                )

    # --------------------------------------------------------
    # 2.3. VIDEO ARTIFACT HANDOFF
    # --------------------------------------------------------

    def test_video_handoff_json_and_path(self):
        """Metadata video phải giữ nguyên khi truyền qua JSON."""

        video = VideoArtifact(
            video_id="vid-01",
            render_job_id="job-01",
            audio_id="audio-01",
            run_id="run-01",
            speech_turn_id="turn-01",
            file_path=(
                "shared_data/runs/run-01/"
                "step2_lipsync/overlays/vid-01.mp4"
            ),
            format="mp4",
            codec="h264",
            duration_ms=3000,
            width_px=1280,
            height_px=720,
            fps=25.0,
            has_audio_track=False,
            created_at=NOW,
        )

        # Chuyển metadata sang JSON.
        payload = json.loads(
            video.model_dump_json()
        )

        # Kiểm tra các định danh dùng để truy vết.
        self.assertEqual(
            payload["audio_id"],
            "audio-01",
        )

        self.assertEqual(
            payload["speech_turn_id"],
            "turn-01",
        )

        self.assertEqual(
            payload["render_job_id"],
            "job-01",
        )

        # Khôi phục VideoArtifact từ JSON.
        restored = VideoArtifact.model_validate(payload)

        self.assertEqual(restored, video)

    # --------------------------------------------------------
    # 2.4. KIỂM TRA TÊN FIELD
    # --------------------------------------------------------

    def test_field_names_stable(self):
        """Không được vô tình đổi tên/xóa field của contract."""

        expected_render_job_fields = {
            "render_job_id",
            "run_id",
            "audio_id",
            "speech_turn_id",
            "source_video_path",
            "avatar_id",
            "license_ref",
            "status",
            "created_at",
            "started_at",
            "finished_at",
            "output_video_id",
            "error_code",
        }

        expected_video_artifact_fields = {
            "video_id",
            "render_job_id",
            "audio_id",
            "run_id",
            "speech_turn_id",
            "file_path",
            "format",
            "codec",
            "duration_ms",
            "width_px",
            "height_px",
            "fps",
            "has_audio_track",
            "created_at",
        }

        self.assertEqual(
            set(RenderJob.model_fields),
            expected_render_job_fields,
        )

        self.assertEqual(
            set(VideoArtifact.model_fields),
            expected_video_artifact_fields,
        )

    # --------------------------------------------------------
    # 2.5. JSON SCHEMA
    # --------------------------------------------------------

    def test_json_schema_generation(self):
        """Hai model phải tạo được JSON Schema hợp lệ."""

        for schema in (RenderJob, VideoArtifact):

            result = schema.model_json_schema()

            # extra="forbid" phải được phản ánh
            # trong JSON Schema.
            self.assertEqual(
                result["additionalProperties"],
                False,
            )

            self.assertTrue(
                result["properties"]
            )


if __name__ == "__main__":
    unittest.main()