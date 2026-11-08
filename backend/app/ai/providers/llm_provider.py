'''LLM provider concrete implementation using OpenAI-compatible API.'''

import os
import json
import logging
from typing import Any, Dict

import httpx
from pydantic import BaseModel, ValidationError

from .base import LLMProvider
from .exceptions import ProviderError, AuthenticationError, RateLimitError, TimeoutError

logger = logging.getLogger("brandcanon")

class OpenAICompatibleLLMProvider(LLMProvider):
    """LLM provider that talks to an OpenAI‑compatible endpoint.

    The endpoint, API key and default model are taken from environment variables:
        LLM_API_BASE (default: https://api.openai.com/v1)
        LLM_API_KEY (required)
        LLM_MODEL   (default: gpt-4o-mini)
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise AuthenticationError("LLM_API_KEY not configured")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = httpx.Client(timeout=30.0)

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = self.client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            logger.error("LLM request error: %s", exc)
            raise TimeoutError(str(exc)) from exc
        if response.status_code == 401:
            raise AuthenticationError("Invalid LLM credentials")
        if response.status_code == 429:
            raise RateLimitError("LLM rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"LLM service error {response.status_code}: {response.text}")
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError("Unable to decode LLM response as JSON") from exc

    def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 1024, **kwargs) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        resp = self._post("chat/completions", payload)
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError("Unexpected LLM response structure") from exc

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Any:
        """Generate JSON adhering to *schema*.

        The method uses the OpenAI function‑calling style: the *schema* is passed as a
        single function definition named ``_response``. The model is forced to
        return a function call payload, which we then validate against the provided
        Pydantic model (or raw schema if a model class is not supplied).
        """
        function_def = {
            "name": "_response",
            "description": "Generate a structured JSON response",
            "parameters": schema,
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 1024,
            "functions": [function_def],
            "function_call": {"name": "_response"},
            **kwargs,
        }
        resp = self._post("chat/completions", payload)
        try:
            function_call = resp["choices"][0]["message"]["function_call"]
            raw_json = function_call["arguments"]
            data = json.loads(raw_json)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ProviderError("Failed to extract structured JSON from LLM response") from exc

        # If a Pydantic model class is supplied in the schema under "pydantic_model"
        # we validate against it; otherwise we perform a simple schema check.
        pydantic_model = schema.get("pydantic_model")
        if pydantic_model and issubclass(pydantic_model, BaseModel):
            try:
                return pydantic_model.parse_obj(data)
            except ValidationError as exc:
                raise ProviderError("Structured response failed validation") from exc
        return data

