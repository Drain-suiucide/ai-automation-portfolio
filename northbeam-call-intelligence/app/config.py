"""Settings (from environment) and the deterministic policy (from YAML)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = Path(__file__).resolve().parent / "policies" / "default.yml"


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Policy:
    max_discount_pct: int
    min_asr_confidence: float
    min_words: int
    consent_probe_seconds: int
    max_upload_mb: int
    allowed_extensions: tuple[str, ...]
    consent_phrases: tuple[str, ...]
    churn_keywords: tuple[str, ...]
    competitors: tuple[str, ...]
    negative_words: tuple[str, ...]
    negative_hits_threshold: int
    positive_words: tuple[str, ...]
    compliance_keywords: tuple[str, ...]
    injection_patterns: tuple[str, ...]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Policy:
        def strs(key: str) -> tuple[str, ...]:
            v = d.get(key, [])
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                raise ConfigError(f"policy.{key} must be a list of strings")
            return tuple(v)

        def num(key: str, kind: type) -> Any:
            v = d.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ConfigError(f"policy.{key} must be a number")
            return kind(v)

        pol = Policy(
            max_discount_pct=num("max_discount_pct", int),
            min_asr_confidence=num("min_asr_confidence", float),
            min_words=num("min_words", int),
            consent_probe_seconds=num("consent_probe_seconds", int),
            max_upload_mb=num("max_upload_mb", int),
            allowed_extensions=tuple(x.lower() for x in strs("allowed_extensions")),
            consent_phrases=strs("consent_phrases"),
            churn_keywords=strs("churn_keywords"),
            competitors=strs("competitors"),
            negative_words=strs("negative_words"),
            negative_hits_threshold=num("negative_hits_threshold", int),
            positive_words=strs("positive_words"),
            compliance_keywords=strs("compliance_keywords"),
            injection_patterns=strs("injection_patterns"),
        )
        for p in pol.injection_patterns:
            try:
                re.compile(p)
            except re.error as exc:
                raise ConfigError(f"bad injection pattern {p!r}: {exc}") from exc
        return pol


def load_policy(path: Path | None = None) -> Policy:
    with open(path or DEFAULT_POLICY, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError("policy file must contain a mapping")
    return Policy.from_dict(data)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    policy_path: Path
    fixtures_dir: Path
    asr_provider: str = "fixture"
    llm_provider: str = "fake"
    retention_days: int = 30

    @property
    def db_path(self) -> Path:
        return self.data_dir / "nci.sqlite3"

    @property
    def blob_dir(self) -> Path:
        return self.data_dir / "blobs"

    @staticmethod
    def from_env(env: dict[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        return Settings(
            data_dir=Path(e.get("NCI_DATA_DIR", ROOT / "data")),
            policy_path=Path(e.get("NCI_POLICY_PATH", DEFAULT_POLICY)),
            fixtures_dir=Path(e.get("NCI_FIXTURES_DIR", ROOT / "evals" / "transcripts")),
            asr_provider=e.get("NCI_ASR_PROVIDER", "fixture"),
            llm_provider=e.get("NCI_LLM_PROVIDER", "fake"),
            retention_days=int(e.get("NCI_RETENTION_DAYS", "30")),
        )
