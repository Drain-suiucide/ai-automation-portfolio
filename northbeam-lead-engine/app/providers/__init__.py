"""Provider interfaces and factories."""

from app.pipeline.draft import FakeLLM, LLMProvider
from app.pipeline.enrich import EnrichmentProvider, FakeWebEnrichment, StaticEnrichment
from app.pipeline.send import MemoryMail, SMTPMail
from app.settings import get_settings


def get_enrichment_provider(pages: dict[str, str] | None = None) -> EnrichmentProvider:
    settings = get_settings()
    if pages is not None or settings.enrichment_provider == "static":
        return StaticEnrichment(pages=pages or {})
    return FakeWebEnrichment()


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    # anthropic / openai / ollama / gateway can be wired later; demo uses fake.
    _ = settings.llm_provider
    return FakeLLM()


def get_mail_provider(*, memory: bool = False) -> SMTPMail | MemoryMail:
    if memory:
        return MemoryMail()
    return SMTPMail()
