"""SQLite store (stdlib). One short-lived connection per operation; audit is append-only
(enforced by triggers) and hash-chained. Swap for PostgreSQL behind the same methods."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.textutil import sha256_hex

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
  id TEXT PRIMARY KEY, external_id TEXT NOT NULL, content_hash TEXT NOT NULL,
  status TEXT NOT NULL, meta TEXT NOT NULL DEFAULT '{}', audio_key TEXT,
  language TEXT, asr_meta TEXT NOT NULL DEFAULT '{}', status_reason TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT,
  UNIQUE (external_id, content_hash));
CREATE TABLE IF NOT EXISTS transcripts (call_id TEXT PRIMARY KEY, segments TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS insights (
  call_id TEXT PRIMARY KEY, data TEXT NOT NULL, report TEXT NOT NULL,
  prompt_version TEXT, provider TEXT, model TEXT);
CREATE TABLE IF NOT EXISTS flags (call_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS crm_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, call_id TEXT NOT NULL, kind TEXT NOT NULL,
  payload TEXT NOT NULL, requires_approval INTEGER NOT NULL, state TEXT NOT NULL, crm_ref TEXT);
CREATE TABLE IF NOT EXISTS approvals (
  call_id TEXT PRIMARY KEY, reviewer_id TEXT NOT NULL, decision TEXT NOT NULL,
  content_hash TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, call_id TEXT, event TEXT NOT NULL,
  data TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
  BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
  BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
"""

GENESIS = "0" * 64


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Store:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=30)
        try:
            conn.executescript(SCHEMA)  # executescript manages its own transaction
        finally:
            conn.close()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    # ---- calls
    def create_call(self, external_id: str, content_hash: str, meta: dict[str, Any],
                    audio_ext: str) -> tuple[dict[str, Any], bool]:
        """Insert a call, or return the existing one for (external_id, content_hash)."""
        with self._conn() as c:
            row = c.execute("SELECT * FROM calls WHERE external_id=? AND content_hash=?",
                            (external_id, content_hash)).fetchone()
            if row:
                return self._call(row), False
            n = c.execute("SELECT COUNT(*) FROM calls").fetchone()[0] + 1
            cid, ts = f"call-{n:04d}", now_iso()
            c.execute(
                "INSERT INTO calls (id, external_id, content_hash, status, meta, audio_key,"
                " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (cid, external_id, content_hash, "received", dumps(meta),
                 f"calls/{n:04d}/audio.{audio_ext}", ts, ts))
            row = c.execute("SELECT * FROM calls WHERE id=?", (cid,)).fetchone()
            return self._call(row), True

    @staticmethod
    def _call(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["meta"] = json.loads(d["meta"])
        d["asr_meta"] = json.loads(d["asr_meta"])
        return d

    def get_call(self, call_id: str) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM calls WHERE id=?", (call_id,)).fetchone()
        return self._call(row) if row else None

    def list_calls(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as c:
            if status:
                rows = c.execute("SELECT * FROM calls WHERE status=? ORDER BY id DESC", (status,))
            else:
                rows = c.execute("SELECT * FROM calls ORDER BY id DESC")
            calls = [self._call(r) for r in rows.fetchall()]
            for call in calls:
                f = c.execute("SELECT data FROM flags WHERE call_id=?", (call["id"],)).fetchone()
                call["flag_codes"] = ([x["code"] for x in json.loads(f["data"])
                                       if x["severity"] == "review"] if f else [])
        return calls

    def update_call(self, call_id: str, **fields: Any) -> None:
        allowed = {"status", "status_reason", "language", "asr_meta", "meta", "audio_key",
                   "deleted_at"}
        if not set(fields) <= allowed:
            raise ValueError("unknown call field")
        vals = {k: (dumps(v) if k in ("asr_meta", "meta") else v) for k, v in fields.items()}
        vals["updated_at"] = now_iso()
        sets = ", ".join(f"{k}=?" for k in vals)
        with self._conn() as c:
            c.execute(f"UPDATE calls SET {sets} WHERE id=?", (*vals.values(), call_id))  # noqa: S608

    # ---- analysis artefacts
    def save_analysis(self, call_id: str, segments: list[dict[str, Any]], insights: dict[str, Any],
                      report: dict[str, Any], flags: list[dict[str, Any]],
                      actions: list[dict[str, Any]], llm: dict[str, Any]) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO transcripts VALUES (?,?)", (call_id, dumps(segments)))
            c.execute("INSERT OR REPLACE INTO insights VALUES (?,?,?,?,?,?)",
                      (call_id, dumps(insights), dumps(report), llm.get("prompt_version"),
                       llm.get("provider"), llm.get("model")))
            c.execute("INSERT OR REPLACE INTO flags VALUES (?,?)", (call_id, dumps(flags)))
            c.execute("DELETE FROM crm_actions WHERE call_id=?", (call_id,))
            for a in actions:
                c.execute("INSERT INTO crm_actions (call_id, kind, payload, requires_approval,"
                          " state, crm_ref) VALUES (?,?,?,?,?,?)",
                          (call_id, a["kind"], dumps(a["payload"]), int(a["requires_approval"]),
                           a["state"], a.get("crm_ref")))

    def save_transcript_only(self, call_id: str, segments: list[dict[str, Any]]) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO transcripts VALUES (?,?)", (call_id, dumps(segments)))

    def get_analysis(self, call_id: str) -> dict[str, Any]:
        with self._conn() as c:
            t = c.execute("SELECT segments FROM transcripts WHERE call_id=?", (call_id,)).fetchone()
            i = c.execute("SELECT * FROM insights WHERE call_id=?", (call_id,)).fetchone()
            f = c.execute("SELECT data FROM flags WHERE call_id=?", (call_id,)).fetchone()
            a = c.execute("SELECT * FROM crm_actions WHERE call_id=? ORDER BY id",
                          (call_id,)).fetchall()
            ap = c.execute("SELECT * FROM approvals WHERE call_id=?", (call_id,)).fetchone()
        return {
            "segments": json.loads(t["segments"]) if t else [],
            "insights": json.loads(i["data"]) if i else None,
            "validation": json.loads(i["report"]) if i else None,
            "llm": {"provider": i["provider"], "model": i["model"],
                    "prompt_version": i["prompt_version"]} if i else None,
            "flags": json.loads(f["data"]) if f else [],
            "actions": [{"id": r["id"], "kind": r["kind"], "payload": json.loads(r["payload"]),
                         "requires_approval": bool(r["requires_approval"]), "state": r["state"],
                         "crm_ref": r["crm_ref"]} for r in a],
            "approval": dict(ap) if ap else None,
        }

    def set_action_state(self, action_id: int, state: str, crm_ref: str | None = None) -> None:
        with self._conn() as c:
            c.execute("UPDATE crm_actions SET state=?, crm_ref=? WHERE id=?",
                      (state, crm_ref, action_id))

    def save_approval(self, call_id: str, reviewer_id: str, decision: str, content_hash: str) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO approvals VALUES (?,?,?,?,?)",
                      (call_id, reviewer_id, decision, content_hash, now_iso()))

    def erase_call_data(self, call_id: str) -> None:
        """Remove every content-bearing row. The `calls` row stays as a tombstone."""
        with self._conn() as c:
            for table in ("transcripts", "insights", "flags", "crm_actions", "approvals"):
                c.execute(f"DELETE FROM {table} WHERE call_id=?", (call_id,))  # noqa: S608

    # ---- audit
    def audit(self, call_id: str | None, event: str, data: dict[str, Any] | None = None) -> None:
        payload = dumps(data or {})
        ts = now_iso()
        with self._conn() as c:
            last = c.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = last["hash"] if last else GENESIS
            h = sha256_hex(f"{prev}|{ts}|{call_id}|{event}|{payload}")
            c.execute("INSERT INTO audit (ts, call_id, event, data, prev_hash, hash)"
                      " VALUES (?,?,?,?,?,?)", (ts, call_id, event, payload, prev, h))

    def audit_events(self, call_id: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as c:
            if call_id:
                rows = c.execute("SELECT * FROM audit WHERE call_id=? ORDER BY seq", (call_id,))
            else:
                rows = c.execute("SELECT * FROM audit ORDER BY seq")
            out = []
            for r in rows.fetchall():
                d = dict(r)
                d["data"] = json.loads(d["data"])
                out.append(d)
        return out

    def verify_audit_chain(self) -> bool:
        prev = GENESIS
        for e in self.audit_events():
            payload = dumps(e["data"])
            if e["prev_hash"] != prev or e["hash"] != sha256_hex(
                    f"{prev}|{e['ts']}|{e['call_id']}|{e['event']}|{payload}"):
                return False
            prev = e["hash"]
        return True

    def dump_text(self) -> str:
        """Every stored string in one blob; used by tests to prove nothing sensitive persists."""
        with self._conn() as c:
            parts = []
            for table in ("calls", "transcripts", "insights", "flags", "crm_actions", "approvals",
                          "audit"):
                for r in c.execute(f"SELECT * FROM {table}").fetchall():  # noqa: S608
                    parts.append(" ".join(str(v) for v in tuple(r)))
        return "\n".join(parts)
