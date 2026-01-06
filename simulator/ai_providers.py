from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class AIResponse:
    next_step_suggestion: str
    risk_warnings: list[str]
    checklist: list[str]


class BaseAIProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_guidance(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def generate_feedback(self, attempt_summary: dict[str, Any]) -> list[str]:
        raise NotImplementedError


class OpenAIProvider(BaseAIProvider):
    def _call(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def generate_guidance(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "Eres un tutor quirúrgico conciso. Devuelve JSON con keys: "
            "next_step_suggestion, risk_warnings, checklist."
        )
        user_prompt = json.dumps(context, ensure_ascii=False)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        data = self._call(payload)
        content = data["choices"][0]["message"]["content"]
        return _safe_parse_guidance(content)

    def generate_feedback(self, attempt_summary: dict[str, Any]) -> list[str]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Genera feedback clínico breve en bullets. Devuelve JSON con key bullets."
                    ),
                },
                {"role": "user", "content": json.dumps(attempt_summary, ensure_ascii=False)},
            ],
            "temperature": 0.3,
        }
        data = self._call(payload)
        content = data["choices"][0]["message"]["content"]
        return _safe_parse_bullets(content)


class GeminiProvider(BaseAIProvider):
    def _call(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def generate_guidance(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Eres tutor quirúrgico. Devuelve JSON con keys: "
            "next_step_suggestion, risk_warnings, checklist.\n\n"
            f"Contexto: {json.dumps(context, ensure_ascii=False)}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        data = self._call(payload)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _safe_parse_guidance(text)

    def generate_feedback(self, attempt_summary: dict[str, Any]) -> list[str]:
        prompt = (
            "Genera feedback clínico breve. Devuelve JSON con key bullets.\n\n"
            f"Resumen: {json.dumps(attempt_summary, ensure_ascii=False)}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        data = self._call(payload)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _safe_parse_bullets(text)


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


def build_provider(provider: str, api_key: str, model: str) -> BaseAIProvider:
    if provider == "GEMINI":
        return GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash")
    return OpenAIProvider(api_key=api_key, model=model or "gpt-4o-mini")
