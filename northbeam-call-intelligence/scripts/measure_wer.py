"""Word error rate of the local ASR on your own recordings (see evals/audio/README.md)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.evaluation import wer  # noqa: E402
from app.pipeline.asr import AudioRef, FasterWhisperASR  # noqa: E402


def main() -> int:
    pairs = [(w, w.with_suffix(".txt")) for w in sorted((ROOT / "evals" / "audio").glob("*.wav"))]
    pairs = [(w, t) for w, t in pairs if t.exists()]
    if not pairs:
        print("no <name>.wav + <name>.txt pairs found in evals/audio/")
        return 2
    asr = FasterWhisperASR()
    scores = []
    for wav, ref in pairs:
        hyp = " ".join(s.text for s in asr.transcribe(AudioRef(wav.stem, wav, wav.name)).segments)
        score = wer(ref.read_text(encoding="utf-8"), hyp)
        scores.append(score)
        print(f"{wav.name}: WER {score:.3f}")
    print(f"mean WER over {len(scores)} file(s): {sum(scores) / len(scores):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
