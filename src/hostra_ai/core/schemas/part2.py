"""Data contracts Part 2 - lip-sync cho HOSTRA AI PoC.

Schema chỉ kiểm tra cấu trúc, định dạng và tính nhất quán nội bộ.
Service kiểm tra quan hệ với AudioArtifact, quyền sử dụng avatar,
sự tồn tại/nội dung file media và chuyển trạng thái RenderJob.
"""

import re
from datetime import datetime
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

from .common import (
    ID_PATTERN,
    normalize_utc,
    validate_relative_media_path,
)


# ============================================================
# 0. KIỂU DỮ LIỆU VÀ CÁC GIỚI HẠN DÙNG CHUNG
# ============================================================

# Bốn trạng thái hợp lệ của một lần render lip-sync.
RenderStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
]

# Giới hạn kỹ thuật của một clip lip-sync trong PoC.
#
# Đây là giới hạn kiểm tra dữ liệu đầu vào metadata,
# không phải tiêu chí đánh giá chất lượng model.
#
# Ví dụ: renderer có thể tạo video 720p, 25 FPS.
# Việc đo chất lượng và benchmark nằm ở service.

MIN_VIDEO_DIMENSION_PX = 64
MAX_VIDEO_DIMENSION_PX = 4096
MAX_VIDEO_FPS = 120.0

# Giới hạn 10 phút cho một clip thoại.
# Không áp dụng cho toàn bộ phiên livestream.
MAX_VIDEO_DURATION_MS = 600_000


# ============================================================
# 1. HÀM KIỂM TRA ĐƯỜNG DẪN DÙNG CHUNG TRONG PART 2
# ============================================================

def _validate_media_path(
    value: str,
    *,
    suffix: str,
) -> str:
    """Kiểm tra đường dẫn media tương đối và chuẩn hóa.

    Các nguyên tắc:
    - Chỉ nhận đường dẫn POSIX tương đối.
    - Không nhận đường dẫn tuyệt đối.
    - Không nhận '..' để tránh directory traversal.
    - Không nhận Windows drive.
    - Không nhận đường dẫn chứa ký tự điều khiển.
    - Kiểm tra đúng phần mở rộng file.
    - Không âm thầm loại bỏ khoảng trắng đầu/cuối.

    Việc kiểm tra file tồn tại thực tế thuộc về service.
    """

    # Tái sử dụng helper đã xây dựng ở common.py.
    result = validate_relative_media_path(
        value,
        suffix=suffix,
    )

    # common.py đang sử dụng .strip().
    #
    # Nếu input chứa khoảng trắng đầu/cuối,
    # helper có thể trả về chuỗi đã bị thay đổi.
    #
    # Data Contract không được âm thầm chỉnh sửa
    # đường dẫn do producer gửi vào.
    if result != value:
        raise ValueError("NON_CANONICAL_MEDIA_PATH")

    return result


# ============================================================
# 2. RENDER JOB
# ============================================================

class RenderJob(BaseModel):
    """Snapshot bất biến của một lần thử render lip-sync.

    RenderJob mô tả:
    - Audio cần render.
    - SpeechTurn tương ứng.
    - Video nguồn.
    - Avatar và giấy phép.
    - Trạng thái xử lý.
    - Thời gian bắt đầu/kết thúc.
    - Video đầu ra hoặc mã lỗi.

    Lưu ý quan trọng:
    - Mỗi lần retry tạo render_job_id mới.
    - Không mutate một snapshot đã tồn tại.
    - Không kiểm tra file hoặc giấy phép thật trong schema.
    - Render Controller chịu trách nhiệm chuyển trạng thái.
    """

    # extra="forbid":
    # Không cho phép producer gửi các field ngoài hợp đồng.
    #
    # frozen=True:
    # Không được thay đổi field sau khi tạo object.
    # Khi đổi trạng thái, service phải tạo snapshot mới.
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # 2.1. THÔNG TIN ĐỊNH DANH VÀ TRUY VẾT
    # --------------------------------------------------------

    # ID duy nhất của một lần thử render.
    #
    # Nếu một job thất bại và được retry,
    # lần retry phải có render_job_id khác.
    render_job_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # ID của phiên demo/livestream.
    # Dùng để liên kết và phân vùng artifact theo phiên.
    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # ID tham chiếu đến AudioArtifact của Part 1.
    #
    # Part 2 chỉ tiếp nhận audio đã được TTS tạo thành công.
    audio_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # ID của SpeechTurn tạo ra audio tương ứng.
    #
    # Giúp Part 3 truy tìm video cho từng lượt thoại
    # mà không bắt buộc phải join qua AudioArtifact.
    #
    # Service phải kiểm tra:
    # RenderJob.speech_turn_id
    # == AudioArtifact.speech_turn_id
    speech_turn_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # 2.2. THÔNG TIN ĐẦU VÀO RENDER
    # --------------------------------------------------------

    # Video gốc của người điều khiển/operator.
    #
    # Ví dụ:
    # shared_data/inputs/base_operator.mp4
    #
    # Đây là video đầu vào,
    # KHÔNG phải video được tạo ra sau lip-sync.
    source_video_path: str = Field(
        min_length=1,
        max_length=255,
        strict=True,
    )

    # ID của avatar/danh tính số sử dụng để render.
    avatar_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Tham chiếu đến giấy phép sử dụng avatar.
    #
    # Chỉ lưu reference tại đây.
    #
    # license_gate.py phải kiểm tra:
    # - Giấy phép có tồn tại không?
    # - Có còn hiệu lực không?
    # - Avatar có được phép sử dụng không?
    # - Phạm vi sử dụng có phù hợp không?
    # - Giấy phép có bị thu hồi không?
    license_ref: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # 2.3. TRẠNG THÁI VÀ THỜI GIAN XỬ LÝ
    # --------------------------------------------------------

    # Trạng thái hiện tại của snapshot.
    #
    # queued:
    #   Job đang chờ xử lý.
    #
    # running:
    #   Worker đang xử lý.
    #
    # succeeded:
    #   Render thành công và đầu ra đã được kiểm tra.
    #
    # failed:
    #   Render hoặc bước kiểm tra thất bại.
    status: RenderStatus

    # Thời điểm tạo job.
    #
    # AwareDatetime yêu cầu datetime có timezone.
    # Validator phía dưới chuyển thời điểm về UTC.
    created_at: AwareDatetime

    # Thời điểm worker bắt đầu xử lý.
    #
    # None nếu job chưa bắt đầu.
    #
    # Field(...) có nghĩa:
    # Bắt buộc phải gửi key started_at,
    # nhưng giá trị được phép là None.
    started_at: AwareDatetime | None = Field(...)

    # Thời điểm job kết thúc.
    #
    # None nếu chưa kết thúc.
    finished_at: AwareDatetime | None = Field(...)

    # --------------------------------------------------------
    # 2.4. KẾT QUẢ RENDER
    # --------------------------------------------------------

    # ID video được tạo thành công.
    #
    # Chỉ được khác None khi status="succeeded".
    output_video_id: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Mã lỗi khi render thất bại.
    #
    # Ví dụ:
    # LICENSE_NOT_ALLOWED
    # SOURCE_VIDEO_INVALID
    # RENDER_FAILED
    # OUTPUT_VALIDATION_FAILED
    #
    # Mã lỗi phải viết HOA, không chứa khoảng trắng.
    # Không lưu stack trace vào error_code.
    error_code: str | None = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Z][A-Z0-9_]*$",
        strict=True,
    )

    # ========================================================
    # 2.5. FIELD VALIDATOR - VIDEO NGUỒN
    # ========================================================

    @field_validator("source_video_path")
    @classmethod
    def validate_source_video_path(
        cls,
        value: str,
    ) -> str:
        """Kiểm tra đường dẫn video nguồn.

        Quy ước được chấp nhận:

        shared_data/inputs/<filename>.mp4

        Không chấp nhận:
        - File ngoài thư mục inputs.
        - Thư mục con bên trong inputs.
        - Tên file có ký tự không hợp lệ.
        - File không phải MP4.
        """

        value = _validate_media_path(
            value,
            suffix=".mp4",
        )

        path = PurePosixPath(value)
        parts = path.parts

        # Đường dẫn hợp lệ phải có đúng 3 thành phần:
        #
        # ("shared_data", "inputs", "base_operator.mp4")
        #
        # Không cho phép:
        # shared_data/inputs/subdir/base_operator.mp4
        if (
            len(parts) != 3
            or parts[:2] != ("shared_data", "inputs")
        ):
            raise ValueError(
                "INVALID_SOURCE_VIDEO_LOCATION"
            )

        # Kiểm tra phần tên file không gồm extension.
        #
        # Hợp lệ:
        # base_operator.mp4
        #
        # Không hợp lệ:
        # base operator (1).mp4
        # base;operator.mp4
        if re.fullmatch(
            ID_PATTERN,
            path.stem,
        ) is None:
            raise ValueError(
                "INVALID_SOURCE_VIDEO_FILENAME"
            )

        return value

    # ========================================================
    # 2.6. FIELD VALIDATOR - TIMESTAMP
    # ========================================================

    @field_validator(
        "created_at",
        "started_at",
        "finished_at",
    )
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Chuẩn hóa timestamp có timezone về UTC."""

        if value is None:
            return None

        return normalize_utc(value)

    # ========================================================
    # 2.7. MODEL VALIDATOR - TÍNH NHẤT QUÁN TRẠNG THÁI
    # ========================================================

    @model_validator(mode="after")
    def validate_status_consistency(self):
        """Kiểm tra tính hợp lệ của một snapshot RenderJob.

        Chỉ kiểm tra các field bên trong cùng bản ghi.

        Không kiểm tra lịch sử chuyển trạng thái.
        Ví dụ:
            queued -> running -> succeeded

        Việc đó thuộc về Render Controller.
        """

        # ----------------------------------------------------
        # A. KIỂM TRA THỨ TỰ THỜI GIAN
        # ----------------------------------------------------

        # Worker không thể bắt đầu trước khi job được tạo.
        if (
            self.started_at is not None
            and self.started_at < self.created_at
        ):
            raise ValueError(
                "STARTED_BEFORE_CREATED"
            )

        if self.finished_at is not None:

            # Không thể kết thúc trước thời điểm tạo.
            if self.finished_at < self.created_at:
                raise ValueError(
                    "FINISHED_BEFORE_CREATED"
                )

            # Nếu đã bắt đầu, thời điểm kết thúc
            # không thể trước thời điểm bắt đầu.
            if (
                self.started_at is not None
                and self.finished_at < self.started_at
            ):
                raise ValueError(
                    "FINISHED_BEFORE_STARTED"
                )

        # ----------------------------------------------------
        # B. TRẠNG THÁI QUEUED
        # ----------------------------------------------------

        if self.status == "queued":

            # Job chưa bắt đầu nên tất cả thông tin
            # về xử lý/kết quả đều phải là None.
            if any(
                value is not None
                for value in (
                    self.started_at,
                    self.finished_at,
                    self.output_video_id,
                    self.error_code,
                )
            ):
                raise ValueError(
                    "INVALID_QUEUED_JOB_STATE"
                )

        # ----------------------------------------------------
        # C. TRẠNG THÁI RUNNING
        # ----------------------------------------------------

        elif self.status == "running":

            # Bắt buộc đã có started_at.
            #
            # Chưa được có:
            # - finished_at
            # - output_video_id
            # - error_code
            if (
                self.started_at is None
                or self.finished_at is not None
                or self.output_video_id is not None
                or self.error_code is not None
            ):
                raise ValueError(
                    "INVALID_RUNNING_JOB_STATE"
                )

        # ----------------------------------------------------
        # D. TRẠNG THÁI SUCCEEDED
        # ----------------------------------------------------

        elif self.status == "succeeded":

            # Thành công bắt buộc có:
            # - started_at
            # - finished_at
            # - output_video_id
            #
            # Không được có error_code.
            if (
                self.started_at is None
                or self.finished_at is None
                or self.output_video_id is None
                or self.error_code is not None
            ):
                raise ValueError(
                    "INVALID_SUCCEEDED_JOB_STATE"
                )

        # ----------------------------------------------------
        # E. TRẠNG THÁI FAILED
        # ----------------------------------------------------

        elif self.status == "failed":

            # Job thất bại bắt buộc có:
            # - finished_at
            # - error_code
            #
            # Không được có output_video_id.
            #
            # started_at có thể là None.
            #
            # Ví dụ: license_gate từ chối job
            # trước khi GPU Worker bắt đầu.
            if (
                self.finished_at is None
                or self.error_code is None
                or self.output_video_id is not None
            ):
                raise ValueError(
                    "INVALID_FAILED_JOB_STATE"
                )

        return self


# ============================================================
# 3. VIDEO ARTIFACT
# ============================================================

class VideoArtifact(BaseModel):
    """Metadata của video lip-sync đã render thành công.

    VideoArtifact chỉ được tạo sau khi:
    - Worker hoàn thành render.
    - File MP4 tồn tại.
    - Metadata được kiểm tra.
    - Video vượt qua kiểm tra đầu ra của service.

    Schema không tự mở file MP4 hoặc gọi FFprobe.

    Part 3 có thể dùng speech_turn_id để tìm video.
    Service phải đối chiếu audio_id với AudioArtifact.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # --------------------------------------------------------
    # 3.1. ĐỊNH DANH VÀ TRUY VẾT
    # --------------------------------------------------------

    # ID video đầu ra.
    # Phải khớp tên file <video_id>.mp4.
    video_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Job đã tạo ra video.
    render_job_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Audio đầu vào được dùng để lip-sync.
    audio_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Phiên demo sở hữu video.
    run_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # Lượt thoại tương ứng.
    #
    # Service phải kiểm tra trường này khớp với
    # AudioArtifact.speech_turn_id.
    speech_turn_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=ID_PATTERN,
        strict=True,
    )

    # --------------------------------------------------------
    # 3.2. THÔNG TIN FILE VIDEO
    # --------------------------------------------------------

    # Đường dẫn MP4 lip-sync đầu ra.
    #
    # Quy ước:
    #
    # shared_data/runs/<run_id>/
    # step2_lipsync/overlays/<video_id>.mp4
    file_path: str = Field(
        min_length=1,
        max_length=255,
        strict=True,
    )

    # Định dạng container.
    # PoC hiện chỉ bàn giao MP4.
    format: Literal["mp4"]

    # Codec video thực tế.
    #
    # Ví dụ: h264
    #
    # Service cần lấy từ FFprobe,
    # không suy ra từ đuôi .mp4.
    codec: str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[a-z0-9_]+$",
        strict=True,
    )

    # --------------------------------------------------------
    # 3.3. THÔNG SỐ KỸ THUẬT
    # --------------------------------------------------------

    # Thời lượng video theo mili giây.
    #
    # > 0 và <= 10 phút cho mỗi clip của PoC.
    duration_ms: int = Field(
        gt=0,
        le=MAX_VIDEO_DURATION_MS,
        strict=True,
    )

    # Chiều rộng khung hình theo pixel.
    width_px: int = Field(
        ge=MIN_VIDEO_DIMENSION_PX,
        le=MAX_VIDEO_DIMENSION_PX,
        strict=True,
    )

    # Chiều cao khung hình theo pixel.
    height_px: int = Field(
        ge=MIN_VIDEO_DIMENSION_PX,
        le=MAX_VIDEO_DIMENSION_PX,
        strict=True,
    )

    # Số khung hình mỗi giây.
    #
    # Chặn:
    # - FPS <= 0
    # - FPS > 120
    # - NaN
    # - Infinity
    #
    # Tránh dữ liệu không hợp lệ gây lỗi
    # tính frame và timecode ở Part 3.
    fps: float = Field(
        gt=0,
        le=MAX_VIDEO_FPS,
        allow_inf_nan=False,
        strict=True,
    )

    # True:
    #   File MP4 đã chứa audio track.
    #
    # False:
    #   Part 3 cần lấy âm thanh từ AudioArtifact.
    #
    # Part 3 phải có chính sách tránh ghép
    # cùng một audio hai lần.
    has_audio_track: bool = Field(
        strict=True,
    )

    # Thời điểm tạo artifact.
    created_at: AwareDatetime

    # ========================================================
    # 3.4. FIELD VALIDATOR - VIDEO PATH
    # ========================================================

    @field_validator("file_path")
    @classmethod
    def validate_video_path(
        cls,
        value: str,
    ) -> str:
        """Kiểm tra cú pháp đường dẫn MP4."""

        return _validate_media_path(
            value,
            suffix=".mp4",
        )

    # ========================================================
    # 3.5. FIELD VALIDATOR - TIMESTAMP
    # ========================================================

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        """Chuẩn hóa created_at về UTC."""

        return normalize_utc(value)

    # ========================================================
    # 3.6. MODEL VALIDATOR - VỊ TRÍ FILE VIDEO
    # ========================================================

    @model_validator(mode="after")
    def validate_video_location(self):
        """Kiểm tra vị trí và tên file MP4.

        Phân biệt hai trường hợp lỗi:

        VIDEO_FILE_OUTSIDE_RUN_DIRECTORY:
            File nằm sai thư mục.

        VIDEO_FILENAME_ID_MISMATCH:
            Tên file không khớp video_id.
        """

        path = PurePosixPath(self.file_path)

        # Cấu trúc thư mục chuẩn của Step 2.
        expected_parent = (
            "shared_data",
            "runs",
            self.run_id,
            "step2_lipsync",
            "overlays",
        )

        # Đường dẫn phải gồm:
        #
        # 5 thành phần thư mục + 1 tên file.
        #
        # Ví dụ:
        # shared_data/runs/run-1/
        # step2_lipsync/overlays/video-1.mp4
        if (
            len(path.parts) != 6
            or path.parts[:-1] != expected_parent
        ):
            raise ValueError(
                "VIDEO_FILE_OUTSIDE_RUN_DIRECTORY"
            )

        # File phải được đặt tên theo video_id.
        #
        # Nếu video_id = "video-1",
        # filename bắt buộc là "video-1.mp4".
        if path.name != f"{self.video_id}.mp4":
            raise ValueError(
                "VIDEO_FILENAME_ID_MISMATCH"
            )

        return self