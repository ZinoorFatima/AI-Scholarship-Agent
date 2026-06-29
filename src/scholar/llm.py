"""Thin wrapper over the Google Gemini SDK for validated, structured output.

Every agent calls :func:`generate_structured`. It uses the ``google-genai``
SDK's structured-output mode: a JSON schema is derived from a Pydantic model
(``response_schema``) and the SDK returns a validated instance via
``response.parsed``. On a transient parse/API error we retry once, feeding the
error back to the model.
"""
from __future__ import annotations

import json
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from .config import get_settings

T = TypeVar("T", bound=BaseModel)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a cached Gemini client (key read from settings/.env)."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env or environment."
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generate_structured(
    *,
    system: str,
    prompt: str,
    schema: type[T],
    model: str,
    client: genai.Client | None = None,
) -> T:
    """Ask Gemini for output matching ``schema`` and return a validated instance.

    Args:
        system: The system instruction — the agent's persona and rules.
        prompt: The user turn — the concrete input for this stage.
        schema: A Pydantic model the response must conform to.
        model: The Gemini model id to use.
        client: Optional client override (used by tests).
    """
    client = client or get_client()
    contents = prompt

    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            parsed = response.parsed
            if not isinstance(parsed, schema):
                raise ValueError(
                    "Model returned no parseable output matching the schema."
                )
            return parsed
        except (errors.APIError, ValueError) as exc:
            last_error = exc
            contents = (
                f"{prompt}\n\nYour previous attempt could not be parsed into the "
                f"required schema. Error: {exc}. Return valid JSON that matches "
                "the schema exactly."
            )

    raise RuntimeError(
        f"Failed to get structured output after 2 attempts: {last_error}"
    )


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of a model response that may include prose/fences."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def generate_grounded(
    *,
    system: str,
    prompt: str,
    schema: type[T],
    model: str,
    client: genai.Client | None = None,
) -> T:
    """Like :func:`generate_structured`, but grounded with Google Search so the
    answer reflects real, current information.

    Grounding can't be combined with forced JSON schema output, so we ask for
    JSON in the prompt and parse it. If grounding is unavailable or the parse
    fails, we fall back to plain structured output (model knowledge only).
    """
    client = client or get_client()
    schema_json = json.dumps(schema.model_json_schema())
    grounded_prompt = (
        f"{prompt}\n\nReturn ONLY a JSON object conforming to this JSON schema "
        f"(use null for unknown fields, no prose, no code fences):\n{schema_json}"
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=grounded_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        return schema.model_validate(_extract_json(response.text))
    except (errors.APIError, ValueError, json.JSONDecodeError):
        # Fall back to non-grounded structured output.
        return generate_structured(
            system=system, prompt=prompt, schema=schema, model=model, client=client
        )
