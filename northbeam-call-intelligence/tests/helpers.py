"""Shared test helpers. Plain functions, no pytest features, so tests run anywhere."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.config import ROOT, Policy, Settings, load_policy
from app.demo import silent_wav
from app.pipeline.asr import ASRResult, AudioRef, FixtureASR
from app.pipeline.crm import MockCRM
from app.pipeline.llm import ExtractionPrompt, FakeLLM, LLMResult
from app.service import CallService, Providers

POLICY = load_policy()
DEMO_FIXTURES = ROOT / "evals" / "transcripts"


class RecordingASR:
    name = "recording-fixture"

    def __init__(self, inner: FixtureASR) -> None:
        self.inner, self.calls = inner, []

    def transcribe(self, audio: AudioRef, max_seconds: float | None = None) -> ASRResult:
        self.calls.append(max_seconds)
        return self.inner.transcribe(audio, max_seconds)


class RecordingLLM:
    """Wraps a provider and keeps every prompt it was given (for PII canary checks)."""

    def __init__(self, inner: Any) -> None:
        self.inner, self.prompts = inner, []
        self.name, self.model = inner.name, inner.model

    def extract(self, prompt: ExtractionPrompt) -> LLMResult:
        self.prompts.append(prompt.text())
        return self.inner.extract(prompt)


class ScriptedLLM:
    """Returns canned output. Each response is a JSON-able dict, a raw string, or a callable."""

    name, model = "scripted", "scripted-1"

    def __init__(self, *responses: Any) -> None:
        self.responses, self.calls = list(responses), 0

    def extract(self, prompt: ExtractionPrompt) -> LLMResult:
        r = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if callable(r):
            r = r(prompt)
        raw = r if isinstance(r, str) else json.dumps(r)
        return LLMResult(raw, self.name, self.model, prompt.version)


class Env:
    def __init__(self, svc: CallService, asr: RecordingASR, llm: Any, crm: MockCRM, root: Path):
        self.svc, self.asr, self.llm, self.crm, self.root = svc, asr, llm, crm, root

    def write_fixture(self, external_id: str, turns: list[tuple[str, str]],
                      conf: float = 0.92) -> None:
        segs, t = [], 0.0
        for i, (who, text) in enumerate(turns, start=1):
            segs.append({"id": f"seg-{i}", "start": t, "end": t + 5.0, "speaker": who,
                         "text": text, "confidence": conf})
            t += 5.5
        (self.root / "fixtures" / f"{external_id}.json").write_text(
            json.dumps({"language": "en", "segments": segs}), encoding="utf-8")

    def register(self, external_id: str, consent: bool | None = True, **over: Any) -> dict[str, Any]:
        meta = {"external_id": external_id, "channel": "phone", "agent_id": "agent-1",
                "customer_company": "Acme Ltd", "recorded_at": "2026-09-29T10:00:00Z",
                "consent_recorded": consent, **over}
        return self.svc.register(meta, audio=silent_wav(), filename="x.wav")


def make_env(llm: Any | None = None, policy: Policy | None = None, demo: bool = True) -> Env:
    root = Path(tempfile.mkdtemp(prefix="nci-test-"))
    fx = root / "fixtures"
    if demo:
        shutil.copytree(DEMO_FIXTURES, fx)
    else:
        fx.mkdir()
    settings = Settings(root / "data", ROOT / "app" / "policies" / "default.yml", fx)
    pol = policy or POLICY
    inner = llm if llm is not None else FakeLLM(pol)
    rec_llm = inner if isinstance(inner, (RecordingLLM, ScriptedLLM)) else RecordingLLM(inner)
    asr, crm = RecordingASR(FixtureASR(fx)), MockCRM()
    svc = CallService(settings, pol, Providers(asr, rec_llm, crm))
    return Env(svc, asr, rec_llm, crm, root)


def raises(exc: type[BaseException], fn: Callable[[], Any]) -> BaseException:
    try:
        fn()
    except exc as e:
        return e
    raise AssertionError(f"expected {exc.__name__}")


def flag_codes(call: dict[str, Any]) -> list[str]:
    return [f["code"] for f in call["flags"] if f["severity"] == "review"]
