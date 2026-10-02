"""JSON logs with a request id. Log lines carry ids and counts only, never transcript text."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime

request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), "level": record.levelname,
               "logger": record.name, "msg": record.getMessage(), "request_id": request_id.get()}
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            out.update(extra)
        return json.dumps(out, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger("nci")
    if root.handlers:
        return
    h = logging.StreamHandler()
    h.setFormatter(JsonFormatter())
    root.addHandler(h)
    root.setLevel(level)
    root.propagate = False
