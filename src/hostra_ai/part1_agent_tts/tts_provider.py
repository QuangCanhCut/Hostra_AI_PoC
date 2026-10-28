"""
M04 - Provider tổng hợp tiếng nói và xử lý WAV cho Part 1.

Luồng: SpeechTurn đã admit -> provider -> WAV -> chuyển mono/resample
-> kiểm tra WAV -> ghi file -> AudioArtifact. AudioArtifact chỉ được trả
về sau khi ghi thành công; duration được đo từ số frame, không ước lượng từ text.

MockTTSProvider tạo khoảng lặng để test, không phải giọng nói thật. Provider
OpenAI cần opt-in riêng và có thể phát sinh chi phí. Module không tự lập lịch
video, không chạy lip-sync và không tự đọc nội dung .env.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import struct
import tempfile
from typing import Protocol
from uuid import uuid4
import wave

import yaml

from hostra_ai.core.schemas.part1 import AudioArtifact, SpeechTurn
from .speech_planner import SpeechAdmission


# ============================================================
# 1. CẤU HÌNH VÀ GIAO DIỆN PROVIDER
# ============================================================

class TTSError(RuntimeError):
    """Lỗi TTS với mã ngắn, tránh đưa request/credentials của provider ra ngoài."""


@dataclass(frozen=True)
class TTSConfig:
    """
    Cấu hình provider, giọng, tốc độ và định dạng audio đầu ra.

    ``live_api_opt_in`` mặc định False; sample rate mặc định 16 kHz chỉ là
    cấu hình PoC, cần xác nhận với worker lip-sync thực tế trước khi tích hợp.
    """
    provider: str
    model: str
    voice: str
    sample_rate_hz: int = 16000
    speed: float = 1.0
    timeout_seconds: float = 30.0
    live_api_opt_in: bool = False

    def __post_init__(self):
        """Kiểm tra phạm vi tham số ngay khi tạo cấu hình."""
        if self.provider not in ('mock', 'openai') or not self.model or not self.voice:
            raise ValueError('Invalid TTS provider, model or voice')
        if type(self.sample_rate_hz) is not int or not 8000 <= self.sample_rate_hz <= 96000:
            raise ValueError('Invalid sample rate')
        if not math.isfinite(self.speed) or not 0.25 <= self.speed <= 4:
            raise ValueError('Invalid speed')
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError('Invalid timeout')
        if type(self.live_api_opt_in) is not bool:
            raise ValueError('live_api_opt_in must be boolean')


def load_tts_config(path: str | Path) -> TTSConfig:
    """Đọc section tts từ YAML được chỉ định, sau đó tạo cấu hình đã kiểm tra."""
    data = yaml.safe_load(Path(path).read_text(encoding='utf-8'))['tts']
    return TTSConfig(provider=data['provider'], model=data['model'], voice=data['voice'],
                     sample_rate_hz=data['sample_rate_hz'], speed=data['speed'],
                     timeout_seconds=data['timeout_seconds'], live_api_opt_in=data['live_api_opt_in'])


class TTSProvider(Protocol):
    """
    Giao diện provider nhận text và trả bytes audio; không quyết định nghiệp vụ.

    Điều kiện được tổng hợp thuộc planner/admission. TTSService chịu trách
    nhiệm kiểm tra và chuẩn hóa dữ liệu WAV mà provider trả về.
    """
    def synthesize(self, text: str, config: TTSConfig) -> bytes: ...


# ============================================================
# 2. PROVIDER OFFLINE VÀ OPENAI
# ============================================================

class MockTTSProvider:
    """Tạo WAV khoảng lặng cho test offline; không đại diện giọng tiếng Việt."""
    def __init__(self, duration_ms: int = 250):
        if type(duration_ms) is not int or duration_ms <= 0:
            raise ValueError('duration_ms must be positive')
        self.duration_ms = duration_ms

    def synthesize(self, text: str, config: TTSConfig) -> bytes:
        """Tạo WAV mono PCM 16-bit với sample rate và thời lượng mock đã chọn."""
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(config.sample_rate_hz)
            wav.writeframes(b'\x00\x00' * round(config.sample_rate_hz * self.duration_ms / 1000))
        return output.getvalue()


class OpenAITTSProvider:
    """
    Adapter Speech API OpenAI; chỉ gọi khi cấu hình opt-in tường minh.

    Đây là tích hợp Speech API hiện có, không phải Realtime API. Request chỉ
    gửi text và cấu hình giọng/model, không gửi viewer_id; lệnh gọi có thể
    phát sinh chi phí. Chất lượng giọng tiếng Việt cần được nghe thử thực tế.
    """
    def __init__(self, *, client=None):
        self._client = client

    def synthesize(self, text: str, config: TTSConfig) -> bytes:
        """
        Yêu cầu WAV từ OpenAI và trả bytes; lỗi được chuyển thành TTSError.

        SDK client được tạo khi cần, có timeout và max_retries=0. Client tiêm
        từ ngoài hỗ trợ test mà không thực hiện request mạng thật.
        """
        if not config.live_api_opt_in or config.provider != 'openai':
            raise TTSError('LIVE_API_NOT_ENABLED')
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(base_url='https://api.openai.com/v1', timeout=config.timeout_seconds, max_retries=0)
            except Exception:
                raise TTSError('OPENAI_CLIENT_ERROR') from None
        try:
            response = self._client.audio.speech.create(model=config.model, voice=config.voice,
                input=text, response_format='wav', speed=config.speed, timeout=config.timeout_seconds)
            payload = response.read()
            if not isinstance(payload, bytes) or not payload:
                raise ValueError('empty audio')
            return payload
        except Exception:
            raise TTSError('OPENAI_SYNTHESIS_FAILED') from None


# ============================================================
# 3. ĐỌC, CHUYỂN ĐỔI VÀ KIỂM TRA WAV
# ============================================================

def _read_wav(data: bytes):
    """
    Đọc và kiểm tra WAV PCM 16-bit, một hoặc hai kênh, có đủ dữ liệu frame.

    WAV nén hoặc sample width khác 2 byte hiện không được hỗ trợ; không thể
    khẳng định mọi định dạng audio từ provider đều chuyển đổi được bằng hàm này.
    """
    try:
        with wave.open(io.BytesIO(data), 'rb') as wav:
            channels, width, rate, frames = wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()
            if wav.getcomptype() != 'NONE' or channels not in (1, 2) or width != 2 or rate < 1 or frames < 1:
                raise ValueError('Unsupported WAV format')
            raw = wav.readframes(frames)
            if len(raw) != frames * channels * width:
                raise ValueError('Truncated WAV')
            return raw, channels, rate, frames
    except (wave.Error, EOFError, ValueError, TypeError, struct.error) as exc:
        raise TTSError('INVALID_WAV') from exc


def normalize_wav(data: bytes, target_rate: int) -> bytes:
    """
    Chuyển PCM 16-bit mono/stereo về mono và resample bằng nội suy tuyến tính.

    Với stereo, mỗi mẫu mono là trung bình hai kênh. Các mẫu mới được tính
    từ vị trí tương ứng trong dữ liệu gốc, không chỉ sửa sample rate ở header.
    Nội suy tuyến tính chưa được đánh giá chất lượng/khử aliasing cho audio thật.
    """
    raw, channels, rate, frames = _read_wav(data)
    values = struct.unpack('<' + 'h' * (frames * channels), raw)
    mono = list(values) if channels == 1 else [(values[2*i] + values[2*i+1]) // 2 for i in range(frames)]
    count = max(1, round(frames * target_rate / rate))
    samples = []
    for i in range(count):
        position = i * rate / target_rate
        left = min(int(position), frames - 1)
        right = min(left + 1, frames - 1)
        value = round(mono[left] + (mono[right] - mono[left]) * (position - left))
        samples.append(max(-32768, min(32767, value)))
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(target_rate)
        wav.writeframes(struct.pack('<' + 'h' * count, *samples))
    return output.getvalue()


def validate_wav(data: bytes, target_rate: int) -> int:
    """
    Kiểm tra WAV đầu ra mono PCM 16-bit, đúng sample rate và duration dương.

    Trả duration_ms = round(số frame * 1000 / sample rate). Nếu dữ liệu không
    đầy đủ hoặc format không phù hợp, hàm phát sinh TTSError.
    """
    _, channels, rate, frames = _read_wav(data)
    if channels != 1 or rate != target_rate:
        raise TTSError('WAV_FORMAT_MISMATCH')
    duration = round(frames * 1000 / rate)
    if duration <= 0:
        raise TTSError('WAV_DURATION_INVALID')
    return duration


# ============================================================
# 4. GHI WAV VÀ BÀN GIAO ARTIFACT/METADATA
# ============================================================

class TTSService:
    """
    Điều phối lượt đã admit, provider, xác thực audio và ghi WAV theo run.

    Đường dẫn trong AudioArtifact là tương đối với workspace. Mỗi file mang
    audio_id riêng; service không tự ghi metadata JSON hay xếp lịch phát.
    """
    def __init__(self, admission: SpeechAdmission, provider: TTSProvider, config: TTSConfig, *, workspace: str | Path):
        self.admission, self.provider, self.config = admission, provider, config
        self.workspace = Path(workspace).resolve()

    def synthesize(self, turn: SpeechTurn) -> AudioArtifact:
        """
        Tiêu thụ admission một lần, tổng hợp, kiểm tra và lưu một WAV.

        Ghi file tạm cùng thư mục rồi tạo hard link tới tên cuối để tránh ghi
        đè. Nếu lỗi, không trả AudioArtifact thành công và dọn file tạm.
        """
        self.admission.consume(turn)
        try:
            payload = self.provider.synthesize(turn.text, self.config)
            converted = normalize_wav(payload, self.config.sample_rate_hz)
            duration = validate_wav(converted, self.config.sample_rate_hz)
        except TTSError:
            raise
        except Exception:
            raise TTSError('SYNTHESIS_FAILED') from None
        audio_id = 'AUDIO-' + uuid4().hex
        relative = f'shared_data/runs/{turn.run_id}/step1_agent_audio/audio/{audio_id}.wav'
        artifact = AudioArtifact(audio_id=audio_id, speech_turn_id=turn.speech_turn_id,
            response_id=turn.response_id, run_id=turn.run_id, voice_id=self.config.voice,
            file_path=relative, format='wav', codec='pcm_s16le', sample_rate_hz=self.config.sample_rate_hz,
            channels=1, duration_ms=duration, created_at=datetime.now(timezone.utc))
        destination = self.workspace.joinpath(*relative.split('/'))
        if not destination.resolve().is_relative_to(self.workspace / 'shared_data' / 'runs' / turn.run_id):
            raise TTSError('UNSAFE_AUDIO_PATH')
        tmp = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.tmp', delete=False) as stream:
                tmp = Path(stream.name)
                stream.write(converted)
                stream.flush()
                os.fsync(stream.fileno())
            validate_wav(tmp.read_bytes(), self.config.sample_rate_hz)
            os.link(tmp, destination)  # Tạo tên đích không ghi đè trên cùng filesystem.
        except OSError:
            raise TTSError('AUDIO_WRITE_FAILED') from None
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        return artifact


def write_run_metadata(workspace: str | Path, run_id: str, turns: list[SpeechTurn],
                       artifacts: list[AudioArtifact]) -> None:
    """
    Chủ động ghi speech_turns.json và audio_artifacts.json cho một run.

    Trước khi ghi, xác thực lại schema, liên kết ID và duration từ file WAV.
    Hàm không ghi đè metadata sẵn có; nếu ghi lỗi sẽ dọn các file do lần gọi
    này vừa tạo. Caller chịu trách nhiệm gọi khi dữ liệu run đã sẵn sàng.
    """
    root = Path(workspace).resolve()
    try:
        turns = [SpeechTurn.model_validate(turn.model_dump()) for turn in turns]
        artifacts = [AudioArtifact.model_validate(item.model_dump()) for item in artifacts]
    except (ValueError, AttributeError, TypeError):
        raise TTSError('INVALID_METADATA') from None
    by_id = {turn.speech_turn_id: turn for turn in turns}
    if len(by_id) != len(turns) or any(turn.run_id != run_id for turn in turns):
        raise TTSError('INVALID_TURN_METADATA')
    if len({a.audio_id for a in artifacts}) != len(artifacts):
        raise TTSError('DUPLICATE_AUDIO_METADATA')
    for item in artifacts:
        turn = by_id.get(item.speech_turn_id)
        if turn is None or item.run_id != run_id or item.response_id != turn.response_id:
            raise TTSError('AUDIO_LINK_MISMATCH')
        path = root.joinpath(*item.file_path.split('/'))
        if not path.resolve().is_relative_to(root / 'shared_data' / 'runs' / run_id):
            raise TTSError('UNSAFE_AUDIO_PATH')
        try:
            duration = validate_wav(path.read_bytes(), item.sample_rate_hz)
        except OSError:
            raise TTSError('AUDIO_FILE_UNAVAILABLE') from None
        if duration != item.duration_ms:
            raise TTSError('AUDIO_METADATA_MISMATCH')
    # Yêu cầu ít nhất một turn đã được model kiểm tra run_id trước khi tạo đường dẫn.
    if not turns:
        raise TTSError('EMPTY_TURN_METADATA')
    directory = root / 'shared_data' / 'runs' / run_id / 'step1_agent_audio'
    if not directory.resolve().is_relative_to(root / 'shared_data' / 'runs' / run_id):
        raise TTSError('UNSAFE_AUDIO_PATH')
    directory.mkdir(parents=True, exist_ok=True)
    created, temps = [], []
    try:
        for name, values in (('speech_turns.json', turns), ('audio_artifacts.json', artifacts)):
            destination = directory / name
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory, suffix='.tmp', delete=False) as stream:
                temps.append(Path(stream.name))
                json.dump([v.model_dump(mode='json') for v in values], stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temps[-1], destination)
            created.append(destination)
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise TTSError('METADATA_WRITE_FAILED') from None
    finally:
        for path in temps:
            path.unlink(missing_ok=True)
