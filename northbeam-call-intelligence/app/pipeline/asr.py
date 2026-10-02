"""ASR providers. `fixture` replays prepared transcripts (CI, demo); `faster_whisper` is local."""

from __future__ import annotations

import array
import json
import math
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.config import Settings
from app.domain import Segment


class ASRError(RuntimeError):
    pass


@dataclass(frozen=True)
class AudioRef:
    external_id: str
    path: Path
    filename: str


@dataclass(frozen=True)
class ASRResult:
    segments: list[Segment]
    language: str
    meta: dict[str, Any]

    @property
    def avg_confidence(self) -> float | None:
        vals = [s.confidence for s in self.segments if s.confidence is not None]
        return sum(vals) / len(vals) if vals else None


class ASRProvider(Protocol):
    name: str

    def transcribe(self, audio: AudioRef, max_seconds: float | None = None) -> ASRResult: ...


class FixtureASR:
    """Looks up <fixtures_dir>/<external_id>.json. The audio bytes are never decoded."""

    name = "fixture"

    def __init__(self, fixtures_dir: Path) -> None:
        self.dir = Path(fixtures_dir)

    def transcribe(self, audio: AudioRef, max_seconds: float | None = None) -> ASRResult:
        path = self.dir / f"{audio.external_id}.json"
        if not path.is_file():
            raise ASRError(f"no transcript fixture for {audio.external_id!r}")
        data = json.loads(path.read_text(encoding="utf-8"))
        segs = [Segment.from_dict(d) for d in data.get("segments", [])]
        if max_seconds is not None:
            segs = [s for s in segs if s.start < max_seconds]
        return ASRResult(segs, str(data.get("language", "en")), {"provider": self.name})


def split_stereo_wav(path: Path, out_dir: Path) -> list[Path]:
    """Split a 16-bit stereo WAV into two mono files (channel 0 = agent, 1 = customer)."""
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 2 or w.getsampwidth() != 2:
            raise ASRError("expected a 16-bit stereo wav")
        rate, frames = w.getframerate(), w.readframes(w.getnframes())
    samples = array.array("h")
    samples.frombytes(frames)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for ch in (0, 1):
        mono = array.array("h", samples[ch::2])
        p = out_dir / f"channel{ch}.wav"
        with wave.open(str(p), "wb") as o:
            o.setnchannels(1)
            o.setsampwidth(2)
            o.setframerate(rate)
            o.writeframes(mono.tobytes())
        paths.append(p)
    return paths


def _is_stereo_wav(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnchannels() == 2
    except (wave.Error, EOFError):
        return False


class FasterWhisperASR:
    """Local ASR. Stereo WAV -> channel 0 = agent, channel 1 = customer. Otherwise 'unknown'.

    Requires the optional extra: `uv sync --extra asr`. Not exercised in CI (model download).
    """

    name = "faster_whisper"

    def __init__(self, model_size: str = "small") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ASRError("faster-whisper is not installed (uv sync --extra asr)") from exc
        self._model = WhisperModel(model_size, compute_type="int8")

    def _run(self, path: Path, speaker: str, max_seconds: float | None) -> tuple[list[dict[str, Any]], str]:
        gen, info = self._model.transcribe(str(path), vad_filter=True)
        rows = []
        for seg in gen:  # lazy generator: stopping early stops decoding
            if max_seconds is not None and seg.start >= max_seconds:
                break
            conf = max(0.0, min(1.0, math.exp(seg.avg_logprob)))
            rows.append({"start": seg.start, "end": seg.end, "speaker": speaker,
                         "text": seg.text.strip(), "confidence": conf})
        return rows, info.language

    def transcribe(self, audio: AudioRef, max_seconds: float | None = None) -> ASRResult:
        import tempfile
        try:
            rows: list[dict[str, Any]] = []
            lang = "en"
            if _is_stereo_wav(audio.path):
                with tempfile.TemporaryDirectory() as tmp:
                    for path, who in zip(split_stereo_wav(audio.path, Path(tmp)),
                                         ("agent", "customer"), strict=True):
                        r, lang = self._run(path, who, max_seconds)
                        rows += r
            else:
                rows, lang = self._run(audio.path, "unknown", max_seconds)
        except ASRError:
            raise
        except Exception as exc:
            raise ASRError(f"transcription failed: {type(exc).__name__}") from exc
        rows.sort(key=lambda r: r["start"])
        segs = [Segment(id=f"seg-{i}", **r) for i, r in enumerate(rows, start=1)]
        return ASRResult(segs, lang, {"provider": self.name})


def build_asr(settings: Settings) -> ASRProvider:
    if settings.asr_provider == "fixture":
        return FixtureASR(settings.fixtures_dir)
    if settings.asr_provider == "faster_whisper":
        import os
        return FasterWhisperASR(os.environ.get("NCI_WHISPER_MODEL", "small"))
    raise ValueError(f"unknown ASR provider {settings.asr_provider!r}")
