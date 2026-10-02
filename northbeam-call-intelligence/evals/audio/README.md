# Real recordings (optional)

The evaluation set is synthetic text replayed through a fixture ASR, so word error rate (WER) is not
measured by default. To measure it on real audio, put pairs here:

    evals/audio/<name>.wav     the recording
    evals/audio/<name>.txt     the reference transcript

then run `uv sync --extra asr && uv run python scripts/measure_wer.py`. Do not commit recordings that
contain real people's voices or personal data.
