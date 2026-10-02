"""Tiny in-process metrics with Prometheus text output (no client library needed)."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.calls: dict[str, int] = defaultdict(int)
        self.stage_sum: dict[str, float] = defaultdict(float)
        self.stage_n: dict[str, int] = defaultdict(int)
        self.stage_samples: dict[str, list[float]] = defaultdict(list)
        self.dropped: dict[str, int] = defaultdict(int)
        self.flags: dict[str, int] = defaultdict(int)
        self.cost_usd = 0.0
        self.tokens = 0

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        t0 = perf_counter()
        try:
            yield
        finally:
            self.observe(name, perf_counter() - t0)

    def observe(self, stage: str, seconds: float) -> None:
        with self._lock:
            self.stage_sum[stage] += seconds
            self.stage_n[stage] += 1
            self.stage_samples[stage].append(seconds)

    def count_call(self, status: str) -> None:
        with self._lock:
            self.calls[status] += 1

    def count_dropped(self, reasons: dict[str, int]) -> None:
        with self._lock:
            for k, v in reasons.items():
                self.dropped[k] += v

    def count_flag(self, code: str) -> None:
        with self._lock:
            self.flags[code] += 1

    def add_llm(self, cost_usd: float, tokens: int) -> None:
        with self._lock:
            self.cost_usd += cost_usd
            self.tokens += tokens

    def percentile(self, stage: str, q: float) -> float:
        s = sorted(self.stage_samples.get(stage, []))
        if not s:
            return 0.0
        return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]

    def render(self) -> str:
        with self._lock:
            lines = ["# TYPE nci_calls_total counter"]
            lines += [f'nci_calls_total{{status="{k}"}} {v}' for k, v in sorted(self.calls.items())]
            lines.append("# TYPE nci_stage_seconds summary")
            for k in sorted(self.stage_sum):
                lines.append(f'nci_stage_seconds_sum{{stage="{k}"}} {self.stage_sum[k]:.6f}')
                lines.append(f'nci_stage_seconds_count{{stage="{k}"}} {self.stage_n[k]}')
            lines.append("# TYPE nci_dropped_claims_total counter")
            lines += [f'nci_dropped_claims_total{{reason="{k}"}} {v}'
                      for k, v in sorted(self.dropped.items())]
            lines.append("# TYPE nci_flags_total counter")
            lines += [f'nci_flags_total{{code="{k}"}} {v}' for k, v in sorted(self.flags.items())]
            lines += ["# TYPE nci_llm_cost_usd_total counter", f"nci_llm_cost_usd_total {self.cost_usd:.6f}",
                      "# TYPE nci_llm_tokens_total counter", f"nci_llm_tokens_total {self.tokens}"]
        return "\n".join(lines) + "\n"
