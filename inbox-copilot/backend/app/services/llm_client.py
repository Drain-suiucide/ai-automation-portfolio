import json
import logging
import time
from typing import Any, Type, TypeVar

import httpx
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
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Exception | None = None

    # --- 1) PRIMARY: Groq через litellm ---
    try:
        t0 = time.perf_counter()
        response = litellm.completion(
            model=PRIMARY_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            api_key=settings.groq_api_key or None,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        content = response.choices[0].message.content or "{}"
        parsed = schema.model_validate_json(content)
        usage = getattr(response, "usage", None)

        return parsed, {
            "model": PRIMARY_MODEL,
            "provider": "groq",
            "latency_ms": latency_ms,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            "cost_usd": None,
            "fallback_used": False,
        }
    except Exception as e:
        logger.warning("Groq call failed: %s", e)
        last_error = e

    # --- 2) FALLBACK: Ollama напрямую через httpx (без litellm) ---
    try:
        ollama_name = FALLBACK_MODEL.split("/", 1)[1]
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

        t0 = time.perf_counter()
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                url,
                json={
                    "model": ollama_name,
                    "messages": messages,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": temperature},
                },
            )
            r.raise_for_status()
            data = r.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        content = (data.get("message") or {}).get("content") or "{}"
        parsed = schema.model_validate_json(content)

        return parsed, {
            "model": FALLBACK_MODEL,
            "provider": "ollama",
            "latency_ms": latency_ms,
            "prompt_tokens": data.get("prompt_eval_count"),
            "completion_tokens": data.get("eval_count"),
            "total_tokens": (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0) or None,
            "cost_usd": 0.0,
            "fallback_used": True,
        }
    except Exception as e:
        logger.warning("Ollama fallback failed: %s", e)
        last_error = e

    raise LLMError(f"All LLM providers failed: {last_error}")