"""INV-2: raw PII never reaches a prompt, a log line, or the database."""

import logging

from app.pipeline.pii import luhn_ok, redact_text
from tests.helpers import make_env

CANARIES = ["jana.novak@brightfield.test", "4111 1111 1111 1111", "4111111111111111",
            "+420 601 234 567", "601 234 567", "four one five five five five zero one two three"]


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage() + " " + str(getattr(record, "fields", "")))


def test_luhn():
    assert luhn_ok("4111111111111111") and not luhn_ok("4111111111111112")


def test_redaction_kinds():
    out, counts = redact_text(
        "mail a.b@x.test, iban DE89 3704 0044 0532 0130 00, card 4111 1111 1111 1111, "
        "call +49 30 1234 5678 or 030 1234 5678")
    assert "@" not in out and "4111" not in out and "DE89" not in out and "1234" not in out
    assert set(counts) == {"EMAIL", "IBAN", "CARD", "PHONE"}


def test_non_luhn_long_number_is_not_called_a_card():
    out, _ = redact_text("account 1234567890123456 ok")
    assert "[NUMBER_1]" in out and "CARD" not in out


def test_spoken_email_and_digits():
    out, counts = redact_text("write to anna dot k at northwind dot test, pin one two three four five six seven eight")
    assert "northwind" not in out and "EMAIL" in counts and "PHONE" in counts


def test_ordinary_numbers_survive():
    text = "We need 40 seats by 2026-10-06 with 25 percent off, that is 1500 euros a month."
    assert redact_text(text)[0] == text


def test_same_value_gets_the_same_token():
    out, _ = redact_text("x@y.test then again x@y.test and z@y.test")
    assert out.count("[EMAIL_1]") == 2 and "[EMAIL_2]" in out


def test_canaries_never_reach_prompt_database_or_logs():
    handler = ListHandler()
    logger = logging.getLogger("nci")
    logger.addHandler(handler)
    try:
        env = make_env()
        call = env.register("demo-pii")
        assert call["status"] == "analyzed"
        blob = "\n".join(env.llm.prompts) + "\n" + env.svc.store.dump_text() + "\n" + "\n".join(handler.lines)
        assert env.llm.prompts, "the model must have been called for this test to mean anything"
        for canary in CANARIES:
            assert canary not in blob, f"raw PII leaked: {canary}"
        assert "[CARD_1]" in blob and "[EMAIL_1]" in blob
        assert call["audit"][3]["event"] == "pii_redacted"
        assert call["audit"][3]["data"]["counts"]["CARD"] == 1
    finally:
        logger.removeHandler(handler)


def test_model_cannot_smuggle_pii_into_free_text():
    from tests.helpers import ScriptedLLM
    llm = ScriptedLLM({"summary": "Contact bob@evil.test", "sentiment": "neutral",
                       "followup_draft": "Call +49 30 1234 5678"})
    env = make_env(llm=llm)
    call = env.register("demo-discovery")
    dump = env.svc.store.dump_text()
    assert "bob@evil.test" not in dump and "1234 5678" not in dump
    assert call["insights"]["summary"] == "Contact [EMAIL_1]"
