from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass
class AIResponse:
    next_step_suggestion: str
    risk_warnings: list[str]
    checklist: list[str]


class AIClient:
    """Cliente IA genérico configurable por settings.

    Para adaptar a un proveedor distinto, ajusta AI_PROVIDER, AI_ENDPOINT y AI_AUTH_SCHEME.
    Si el proveedor no es compatible con OpenAI, adapta _extract_text_from_response.
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.provider = settings.AI_PROVIDER
        self.endpoint = settings.AI_ENDPOINT
        self.default_model = settings.AI_DEFAULT_MODEL
        self.auth_scheme = settings.AI_AUTH_SCHEME
        self.timeout = settings.AI_TIMEOUT_SECONDS

    def generate_guidance(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "Eres un tutor quirúrgico conciso. Devuelve JSON con keys: "
            "next_step_suggestion, risk_warnings, checklist."
        )
        user_prompt = json.dumps(context, ensure_ascii=False)
        payload = self._build_payload(system_prompt, user_prompt, temperature=0.2)
        data = self._post(payload)
        content = self._extract_text_from_response(data)
        return _safe_parse_guidance(content)

    def generate_feedback(self, attempt_summary: dict[str, Any]) -> list[str]:
        system_prompt = "Genera feedback clínico breve en bullets. Devuelve JSON con key bullets."
        user_prompt = json.dumps(attempt_summary, ensure_ascii=False)
        payload = self._build_payload(system_prompt, user_prompt, temperature=0.3)
        data = self._post(payload)
        content = self._extract_text_from_response(data)
        return _safe_parse_bullets(content)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_scheme == "bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.auth_scheme == "x-api-key":
            headers["x-api-key"] = self.api_key
        return headers

    def _params(self) -> dict[str, str]:
        if self.auth_scheme == "query":
            return {"key": self.api_key}
        return {}

    def _build_payload(self, system_prompt: str, user_prompt: str, temperature: float) -> dict[str, Any]:
        if self.provider == "gemini":
            prompt = f"{system_prompt}\n\n{user_prompt}"
            return {"contents": [{"parts": [{"text": prompt}]}]}
        return {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            params=self._params(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _extract_text_from_response(self, data: dict[str, Any]) -> str:
        if self.provider == "gemini":
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return data["choices"][0]["message"]["content"]


def _safe_parse_guidance(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        return {
            "next_step_suggestion": parsed.get("next_step_suggestion", "Continúa con el paso actual."),
            "risk_warnings": parsed.get("risk_warnings", []),
            "checklist": parsed.get("checklist", []),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "next_step_suggestion": text.strip()[:180],
            "risk_warnings": [],
            "checklist": [],
        }


def _safe_parse_bullets(text: str) -> list[str]:
    try:
        parsed = json.loads(text)
        bullets = parsed.get("bullets")
        if isinstance(bullets, list):
            return bullets
    except (json.JSONDecodeError, TypeError):
        pass
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()][:6]


def build_provider(provider: str, api_key: str, model: str) -> AIClient:
    del provider
    del model
    return AIClient(api_key=api_key)
