"""INV-7: after DELETE nothing content-bearing remains; the audit tombstone does."""

import sqlite3
from datetime import UTC, datetime, timedelta

from app.domain import ConflictError
from tests.helpers import make_env, raises

CONTENT_TABLES = ("transcripts", "insights", "flags", "crm_actions", "approvals")


def _count(env, table, call_id):
    with sqlite3.connect(env.svc.store.path) as c:
        return c.execute(f"SELECT COUNT(*) FROM {table} WHERE call_id=?", (call_id,)).fetchone()[0]  # noqa: S608


def test_delete_removes_audio_text_insights_and_crm_records():
    env = make_env()
    call = env.register("demo-discovery")
    env.svc.decide(call["id"], "m-1", "approve", call["review_hash"])
    assert env.crm.records and env.svc.blobs.all_keys()
    words = [s["text"] for s in call["segments"]][2]
    out = env.svc.delete(call["id"])
    assert out["status"] == "deleted" and out["segments"] == [] and out["insights"] is None
    assert env.svc.blobs.all_keys() == []
    assert all(_count(env, t, call["id"]) == 0 for t in CONTENT_TABLES)
    assert env.crm.records == []
    dump = env.svc.store.dump_text()
    assert words not in dump and "Demo Discovery Ltd" not in dump and "quote" not in dump.lower()


def test_tombstone_and_audit_survive_without_content():
    env = make_env()
    call = env.register("demo-discovery")
    out = env.svc.delete(call["id"])
    events = [e["event"] for e in out["audit"]]
    assert events[-1] == "deleted" and out["audit"][-1]["data"]["content_hash"] == call["content_hash"]
    assert out["meta"] == {} and out["deleted_at"]
    assert env.svc.store.verify_audit_chain()


def test_delete_is_idempotent_and_blocks_further_actions():
    env = make_env()
    call = env.register("demo-discovery")
    env.svc.delete(call["id"])
    assert env.svc.delete(call["id"])["status"] == "deleted"
    raises(ConflictError, lambda: env.svc.decide(call["id"], "m-1", "approve"))
    raises(ConflictError, lambda: env.svc.process(call["id"]))


def test_reuploading_the_same_recording_does_not_resurrect_a_deleted_call():
    env = make_env()
    first = env.register("demo-discovery")
    env.svc.delete(first["id"])
    again = env.register("demo-discovery")
    assert again["id"] == first["id"] and again["status"] == "deleted" and again["idempotent"]
    assert env.svc.blobs.all_keys() == []


def test_retention_deletes_only_old_calls():
    env = make_env()
    old = env.register("demo-discovery")
    env.register("demo-pii")
    out = env.svc.run_retention(now=datetime.now(UTC) + timedelta(days=29))
    assert out["deleted"] == []
    out = env.svc.run_retention(now=datetime.now(UTC) + timedelta(days=31))
    assert old["id"] in out["deleted"] and len(out["deleted"]) == 2
    assert env.svc.get(old["id"])["status_reason"] == "retention"
    assert env.svc.blobs.all_keys() == []


def test_audit_log_is_append_only_and_tamper_evident():
    env = make_env()
    env.register("demo-discovery")
    con = sqlite3.connect(env.svc.store.path)
    for sql in ("UPDATE audit SET event='x'", "DELETE FROM audit"):
        try:
            con.execute(sql)
        except sqlite3.DatabaseError as e:
            assert "append-only" in str(e)
        else:
            raise AssertionError(f"{sql} was allowed")
    con.execute("DROP TRIGGER audit_no_update")
    con.execute("UPDATE audit SET data='{\"forged\":1}' WHERE seq=1")
    con.commit()
    assert not env.svc.store.verify_audit_chain()
