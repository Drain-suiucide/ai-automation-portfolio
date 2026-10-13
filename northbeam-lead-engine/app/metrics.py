from __future__ import annotations

from prometheus_client import Counter, Histogram

REQUESTS = Counter("lead_engine_requests_total", "HTTP requests", ["method", "path"])
SENDS = Counter("lead_engine_sends_total", "Outbound sends", ["result"])
BLOCKS = Counter("lead_engine_blocks_total", "Send-guard blocks", ["reason"])
STAGE_LATENCY = Histogram(
    "lead_engine_stage_seconds",
    "Pipeline stage latency",
    ["stage"],
)


def observe_send(result: str) -> None:
    SENDS.labels(result=result).inc()


def observe_block(reason: str) -> None:
    BLOCKS.labels(reason=reason).inc()
