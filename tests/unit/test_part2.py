"""Unit test các field, validator và invariant của Part 2.

Đặt file tại tests/unit/test_part2.py.

Các test sử dụng dữ liệu giả lập.
Không cần GPU, FFmpeg hoặc file media thật.
"""

import unittest
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from hostra_ai.core.schemas.part2 import RenderJob, VideoArtifact


# ============================================================
# 1. DỮ LIỆU MẪU DÙNG CHO TEST
# ============================================================

# Thời điểm chuẩn UTC.
T0 = datetime(
    2026, 10, 25, 1, 0,
    tzinfo=timezone.utc,
)


def make_job(**changes):
    """Tạo một RenderJob hợp lệ để phục vụ unit test.

    Các field truyền qua changes sẽ ghi đè dữ liệu mặc định.
    Nhờ vậy, mỗi test chỉ cần thay field muốn kiểm tra.
    """

    values = {
        "render_job_id": "job-1",
        "run_id": "run-1",
        "audio_id": "audio-1",
        "speech_turn_id": "turn-1",
        "source_video_path": "shared_data/inputs/base_operator.mp4",
        "avatar_id": "avatar-1",
        "license_ref": "license-1",
        "status": "queued",
        "created_at": T0,
        "started_at": None,
        "finished_at": None,
        "output_video_id": None,
        "error_code": None,
    }

    values.update(changes)

    return RenderJob(**values)


def make_video(**changes):
    """Tạo VideoArtifact hợp lệ để phục vụ unit test."""

    values = {
        "video_id": "video-1",
        "render_job_id": "job-1",
        "audio_id": "audio-1",
        "speech_turn_id": "turn-1",
        "run_id": "run-1",
        "file_path": (
            "shared_data/runs/run-1/"
            "step2_lipsync/overlays/video-1.mp4"
        ),
        "format": "mp4",
        "codec": "h264",
        "duration_ms": 2900,
        "width_px": 1280,
        "height_px": 720,
        "fps": 25.0,
        "has_audio_track": False,
        "created_at": T0 + timedelta(seconds=3),
    }

    values.update(changes)

    return VideoArtifact(**values)


# ============================================================
# 2. UNIT TEST - RENDER JOB
# ============================================================

class TestRenderJob(unittest.TestCase):

    # --------------------------------------------------------
    # 2.1. KIỂM TRA CÁC TRẠNG THÁI HỢP LỆ
    # --------------------------------------------------------

    def test_queued(self):
        """Job mới tạo phải được phép ở trạng thái queued."""

        job = make_job()

        self.assertEqual(job.status, "queued")

    def test_running(self):
        """Running phải có thời điểm bắt đầu."""

        job = make_job(
            status="running",
            started_at=T0,
        )

        self.assertEqual(job.status, "running")

    def test_succeeded(self):
        """Succeeded phải có thời điểm và video đầu ra."""

        job = make_job(
            status="succeeded",
            started_at=T0,
            finished_at=T0 + timedelta(seconds=3),
            output_video_id="video-1",
        )

        self.assertEqual(
            job.output_video_id,
            "video-1",
        )

    def test_failed_before_worker_started(self):
        """Cho phép thất bại trước khi Worker bắt đầu.

        Ví dụ:
        License Gate từ chối do giấy phép không hợp lệ.
        """

        job = make_job(
            status="failed",
            finished_at=T0 + timedelta(seconds=1),
            error_code="LICENSE_NOT_ALLOWED",
        )

        self.assertIsNone(job.started_at)

    def test_failed_after_worker_started(self):
        """Cho phép job thất bại sau khi Worker đã bắt đầu."""

        job = make_job(
            status="failed",
            started_at=T0,
            finished_at=T0 + timedelta(seconds=1),
            error_code="RENDER_FAILED",
        )

        self.assertEqual(job.status, "failed")

    # --------------------------------------------------------
    # 2.2. KIỂM TRA TỔ HỢP TRẠNG THÁI KHÔNG HỢP LỆ
    # --------------------------------------------------------

    def test_invalid_status_combinations(self):
        """Từ chối các trạng thái có field mâu thuẫn."""

        invalid_cases = [
            # Queued không được có started_at.
            {
                "status": "queued",
                "started_at": T0,
            },

            # Queued không được có error_code.
            {
                "status": "queued",
                "error_code": "ERROR",
            },

            # Running bắt buộc có started_at.
            {
                "status": "running",
            },

            # Running không được có finished_at.
            {
                "status": "running",
                "started_at": T0,
                "finished_at": T0,
            },

            # Running không được có output_video_id.
            {
                "status": "running",
                "started_at": T0,
                "output_video_id": "video-1",
            },

            # Succeeded bắt buộc có output_video_id.
            {
                "status": "succeeded",
                "started_at": T0,
                "finished_at": T0,
            },

            # Succeeded không được có error_code.
            {
                "status": "succeeded",
                "started_at": T0,
                "finished_at": T0,
                "output_video_id": "video-1",
                "error_code": "ERR",
            },

            # Failed bắt buộc có finished_at.
            {
                "status": "failed",
                "error_code": "ERR",
            },

            # Failed bắt buộc có error_code.
            {
                "status": "failed",
                "finished_at": T0,
            },

            # Failed không được có video đầu ra.
            {
                "status": "failed",
                "finished_at": T0,
                "error_code": "ERR",
                "output_video_id": "video-1",
            },
        ]

        for changes in invalid_cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValidationError):
                    make_job(**changes)

    # --------------------------------------------------------
    # 2.3. KIỂM TRA THỜI GIAN
    # --------------------------------------------------------

    def test_time_order(self):
        """Từ chối các timestamp không đúng thứ tự."""

        invalid_cases = [
            # Bắt đầu trước khi tạo.
            {
                "status": "running",
                "started_at": T0 - timedelta(milliseconds=1),
            },

            # Kết thúc trước khi tạo.
            {
                "status": "failed",
                "finished_at": T0 - timedelta(milliseconds=1),
                "error_code": "ERROR",
            },

            # Kết thúc trước khi bắt đầu.
            {
                "status": "failed",
                "started_at": T0 + timedelta(seconds=2),
                "finished_at": T0 + timedelta(seconds=1),
                "error_code": "ERROR",
            },
        ]

        for changes in invalid_cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValidationError):
                    make_job(**changes)

    def test_utc_conversion(self):
        """Timestamp GMT+7 phải chuyển chính xác về UTC."""

        local = datetime(
            2026, 10, 25, 8,
            tzinfo=timezone(timedelta(hours=7)),
        )

        job = make_job(created_at=local)

        self.assertEqual(job.created_at, T0)

        self.assertEqual(
            job.created_at.utcoffset(),
            timedelta(0),
        )

    def test_naive_timestamp_rejected(self):
        """Không chấp nhận datetime thiếu timezone."""

        with self.assertRaises(ValidationError):
            make_job(
                created_at=datetime(2026, 10, 25, 1)
            )

    # --------------------------------------------------------
    # 2.4. KIỂM TRA ĐỊNH DANH
    # --------------------------------------------------------

    def test_invalid_ids(self):
        """ID không được rỗng, sai pattern hoặc sai kiểu."""

        invalid_ids = [
            "",
            "has space",
            "/etc/passwd",
            "../escape",
            "x" * 65,
            23,
        ]

        for invalid in invalid_ids:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    make_job(audio_id=invalid)

    def test_invalid_speech_turn_id(self):
        """speech_turn_id phải tuân thủ ID_PATTERN."""

        invalid_ids = [
            "",
            "with space",
            "../turn",
            123,
        ]

        for invalid in invalid_ids:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    make_job(speech_turn_id=invalid)

    def test_error_code_pattern(self):
        """Mã lỗi bắt buộc có định dạng viết HOA."""

        invalid_codes = [
            "lowercase",
            "BAD CODE",
            "_START",
            "a" * 65,
            123,
        ]

        for invalid in invalid_codes:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    make_job(
                        status="failed",
                        finished_at=T0,
                        error_code=invalid,
                    )

    # --------------------------------------------------------
    # 2.5. KIỂM TRA FROZEN VÀ EXTRA FORBID
    # --------------------------------------------------------

    def test_unexpected_field_and_frozen(self):
        """Không cho thêm field hoặc mutate snapshot."""

        # Từ chối field không khai báo.
        with self.assertRaises(ValidationError):
            make_job(unexpected="x")

        # Từ chối thay đổi trạng thái trực tiếp.
        with self.assertRaises(ValidationError):
            make_job().status = "running"

    # --------------------------------------------------------
    # 2.6. KIỂM TRA VIDEO NGUỒN
    # --------------------------------------------------------

    def test_source_video_path(self):
        """Từ chối các đường dẫn nguồn không hợp lệ."""

        rejected = [
            "base_operator.mp4",
            "/shared_data/inputs/base_operator.mp4",
            "shared_data/runs/run-1/base.mp4",
            "shared_data/inputs/../x.mp4",
            "shared_data/inputs\\base.mp4",
            "shared_data/inputs/base.mov",
            " shared_data/inputs/base.mp4",
            "shared_data/inputs/base.mp4 ",
            "shared_data/inputs//base.mp4",
            "C:/video/base.mp4",

            # Không nhận thư mục con.
            "shared_data/inputs/subdir/base.mp4",

            # Không nhận filename chứa ký tự lạ.
            "shared_data/inputs/base operator (1).mp4",
            "shared_data/inputs/base;rm.mp4",
        ]

        for path in rejected:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError):
                    make_job(source_video_path=path)

    def test_source_video_filename_error_code(self):
        """Sai tên file phải trả về đúng mã lỗi."""

        with self.assertRaisesRegex(
            ValidationError,
            "INVALID_SOURCE_VIDEO_FILENAME",
        ):
            make_job(
                source_video_path=(
                    "shared_data/inputs/bad name.mp4"
                )
            )

    def test_source_video_nested_directory_error_code(self):
        """Thư mục con phải bị từ chối."""

        with self.assertRaisesRegex(
            ValidationError,
            "INVALID_SOURCE_VIDEO_LOCATION",
        ):
            make_job(
                source_video_path=(
                    "shared_data/inputs/sub/base.mp4"
                )
            )


# ============================================================
# 3. UNIT TEST - VIDEO ARTIFACT
# ============================================================

class TestVideoArtifact(unittest.TestCase):

    # --------------------------------------------------------
    # 3.1. VIDEO HỢP LỆ
    # --------------------------------------------------------

    def test_valid_video(self):
        """VideoArtifact hợp lệ phải được khởi tạo."""

        video = make_video()

        self.assertEqual(video.format, "mp4")

    # --------------------------------------------------------
    # 3.2. KIỂM TRA ĐƯỜNG DẪN
    # --------------------------------------------------------

    def test_bad_location(self):
        """Từ chối đường dẫn sai thư mục hoặc sai tên."""

        bad_paths = [
            # Sai run_id.
            (
                "shared_data/runs/run-OTHER/"
                "step2_lipsync/overlays/video-1.mp4"
            ),

            # Nhầm thư mục Step 3.
            (
                "shared_data/runs/run-1/"
                "step3_composed_video/video-1.mp4"
            ),

            # Sai tên file.
            (
                "shared_data/runs/run-1/"
                "step2_lipsync/overlays/other.mp4"
            ),

            # Sai extension.
            (
                "shared_data/runs/run-1/"
                "step2_lipsync/overlays/video-1.avi"
            ),

            # Directory traversal.
            (
                "../shared_data/runs/run-1/"
                "step2_lipsync/overlays/video-1.mp4"
            ),

            # Khoảng trắng cuối đường dẫn.
            (
                "shared_data/runs/run-1/"
                "step2_lipsync/overlays/video-1.mp4 "
            ),

            # Thiếu thư mục overlays.
            (
                "shared_data/runs/run-1/"
                "step2_lipsync/video-1.mp4"
            ),
        ]

        for path in bad_paths:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError):
                    make_video(file_path=path)

    def test_directory_and_filename_errors_are_separate(self):
        """Phân biệt lỗi sai thư mục và sai filename."""

        with self.assertRaisesRegex(
            ValidationError,
            "VIDEO_FILE_OUTSIDE_RUN_DIRECTORY",
        ):
            make_video(
                file_path=(
                    "shared_data/runs/other/"
                    "step2_lipsync/overlays/video-1.mp4"
                )
            )

        with self.assertRaisesRegex(
            ValidationError,
            "VIDEO_FILENAME_ID_MISMATCH",
        ):
            make_video(
                file_path=(
                    "shared_data/runs/run-1/"
                    "step2_lipsync/overlays/other.mp4"
                )
            )

    # --------------------------------------------------------
    # 3.3. KIỂM TRA THÔNG SỐ KỸ THUẬT
    # --------------------------------------------------------

    def test_invalid_video_technical_metadata(self):
        """Từ chối metadata không hợp lệ."""

        bad_cases = [
            {"format": "mkv"},
            {"codec": "H.264"},
            {"duration_ms": 0},
            {"duration_ms": True},
            {"duration_ms": 600_001},
            {"width_px": -1},
            {"height_px": 0},
            {"width_px": 63},
            {"height_px": 4097},
            {"fps": 0.0},
            {"fps": 120.01},
            {"fps": float("inf")},
            {"fps": float("nan")},
            {"has_audio_track": 1},
        ]

        for changes in bad_cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValidationError):
                    make_video(**changes)

    def test_valid_video_metadata_at_boundaries(self):
        """Các giá trị đúng tại biên phải được chấp nhận."""

        video = make_video(
            duration_ms=600_000,
            width_px=64,
            height_px=4096,
            fps=120.0,
        )

        self.assertEqual(
            video.duration_ms,
            600_000,
        )

    # --------------------------------------------------------
    # 3.4. KIỂM TRA SPEECH TURN
    # --------------------------------------------------------

    def test_invalid_video_speech_turn_id(self):
        """Không nhận speech_turn_id sai pattern."""

        with self.assertRaises(ValidationError):
            make_video(speech_turn_id="turn/2")

    # --------------------------------------------------------
    # 3.5. KIỂM TRA IMMUTABILITY
    # --------------------------------------------------------

    def test_frozen_and_extra_forbidden(self):
        """VideoArtifact không được mutate hoặc thêm field."""

        with self.assertRaises(ValidationError):
            make_video().fps = 30.0

        with self.assertRaises(ValidationError):
            make_video(unknown=True)

    # --------------------------------------------------------
    # 3.6. KIỂM TRA TIMESTAMP
    # --------------------------------------------------------

    def test_video_utc_and_naive_time(self):
        """Chuyển UTC và từ chối timestamp thiếu timezone."""

        local = datetime(
            2026, 10, 25, 10, 0,
            tzinfo=timezone(timedelta(hours=7)),
        )

        self.assertEqual(
            make_video(created_at=local).created_at,
            T0 + timedelta(hours=2),
        )

        with self.assertRaises(ValidationError):
            make_video(
                created_at=datetime(
                    2026, 10, 25, 10, 0
                )
            )


if __name__ == "__main__":
    unittest.main()