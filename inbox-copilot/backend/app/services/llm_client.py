import logging
import time
from typing import Any, Type, TypeVar

import litellm
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

PRIMARY_MODEL = "groq/openai/gpt-oss-120b"
FALLBACK_MODEL = "ollama/llama3.1:8b"


class LLMError(RuntimeError):
    pass


def structured_completion(
    *,
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> tuple[T, dict]:
    """Возвращает (parsed_schema_instance, meta). При ошибке — fallback на Ollama."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Exception | None = None
    fallback_used = False

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            t0 = time.perf_counter()
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                api_key=settings.groq_api_key or None,
                api_base=settings.ollama_base_url if model.startswith("ollama/") else None,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)

            content = response.choices[0].message.content or "{}"
            parsed = schema.model_validate_json(content)

            usage = getattr(response, "usage", None)
            meta = {
                "model": model,
                "provider": model.split("/", 1)[0],
                "latency_ms": latency_ms,
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
                "cost_usd": None,  # Groq free tier = 0
                "fallback_used": fallback_used,
            }
            return parsed, meta

        except Exception as e:
            logger.warning("LLM call failed on %s: %s", model, e)
            last_error = e
            fallback_used = True
            continue

    raise LLMError(f"All LLM providers failed: {last_error}")