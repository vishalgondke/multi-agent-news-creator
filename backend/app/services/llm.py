"""LLM wrapper supporting OpenAI and Google Gemini, with JSON helpers.

Provider is chosen by settings.resolved_provider (LLM_PROVIDER + which key is set).
Falls back to deterministic mock output when MOCK_MODE is on or no key is set,
so the whole pipeline runs end-to-end without credentials.
"""
from __future__ import annotations

import json
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

_openai_client = None
_gemini_client = None
_groq_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai

        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


def _get_groq():
    # Groq exposes an OpenAI-compatible API, so reuse the OpenAI SDK.
    global _groq_client
    if _groq_client is None:
        from openai import OpenAI

        _groq_client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq_client


def _extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of a model response."""
    text = text.strip()
    # strip ```json fences
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _call_openai_compatible(client, model: str, system: str, user: str, max_tokens: int) -> str:
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_openai(system: str, user: str, max_tokens: int) -> str:
    return _call_openai_compatible(
        _get_openai(), settings.openai_model, system, user, max_tokens
    )


def _call_groq(system: str, user: str, max_tokens: int) -> str:
    return _call_openai_compatible(
        _get_groq(), settings.groq_model, system, user, max_tokens
    )


def _call_gemini(system: str, user: str, max_tokens: int) -> str:
    from google.genai import types

    client = _get_gemini()
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    return resp.text or ""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def complete_json(
    *,
    system: str,
    user: str,
    max_tokens: int = 1500,
    mock_fn=None,
) -> Any:
    """Call the configured LLM provider and parse a JSON response."""
    if settings.mock_llm:
        if mock_fn is None:
            raise RuntimeError("MOCK mode but no mock_fn provided")
        return mock_fn()

    provider = settings.resolved_provider
    if provider == "gemini":
        text = _call_gemini(system, user, max_tokens)
    elif provider == "groq":
        text = _call_groq(system, user, max_tokens)
    else:  # openai
        text = _call_openai(system, user, max_tokens)
    return _extract_json(text)
