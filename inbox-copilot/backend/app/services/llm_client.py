import logging
import time
from typing import TypeVar

import httpx
import litellm
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

PROVIDERS: list[tuple[str, str]] = [
    # Быстрые instruct-модели с поддержкой structured output
    ("openrouter", "openrouter/meta-llama/llama-3.3-70b-instruct:free"),
    ("openrouter", "openrouter/google/gemma-4-26b-a4b-it:free"),
    ("openrouter", "openrouter/nvidia/nemotron-3-super-120b-a12b:free"),
    ("openrouter", "openrouter/deepseek/deepseek-v4-flash:free"),
    # Offline fallback
    ("ollama",     "ollama/llama3.2:3b"),
]

class LLMError(RuntimeError):
    pass


def _call_openrouter(model: str, messages: list[dict], temperature: float, max_tokens: int) -> dict:
    t0 = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        api_key=settings.openrouter_api_key or None,
    )
    logger.info("OpenRouter picked model: %s", getattr(response, "model", "unknown"))
    latency_ms = int((time.perf_counter() - t0) * 1000)
    usage = getattr(response, "usage", None)
    return {
        "content": response.choices[0].message.content or "{}",
        "meta": {
            "model": model,
            "provider": "openrouter",
            "latency_ms": latency_ms,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            "cost_usd": None,
            "fallback_used": False,
        },
    }


def _call_ollama(model: str, messages: list[dict], temperature: float) -> dict:
    ollama_name = model.split("/", 1)[1]
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

    prompt_tokens = data.get("prompt_eval_count") or 0
    completion_tokens = data.get("eval_count") or 0
    return {
        "content": (data.get("message") or {}).get("content") or "{}",
        "meta": {
            "model": model,
            "provider": "ollama",
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens or None,
            "completion_tokens": completion_tokens or None,
            "total_tokens": (prompt_tokens + completion_tokens) or None,
            "cost_usd": 0.0,
            "fallback_used": False,
        },
    }


def structured_completion[T: BaseModel](
    *,
    schema: type[T],
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
    primary_provider = PROVIDERS[0][0]

    for provider, model in PROVIDERS:
        try:
            if provider == "ollama":
                out = _call_ollama(model, messages, temperature)
            else:
                out = _call_openrouter(model, messages, temperature, max_tokens)

            parsed = schema.model_validate_json(out["content"])
            meta = out["meta"]
            meta["fallback_used"] = provider != primary_provider
            return parsed, meta

        except Exception as e:
            logger.warning("LLM call failed on %s (%s): %s", provider, model, e)
            last_error = e
            continue

    raise LLMError(f"All LLM providers failed: {last_error}")