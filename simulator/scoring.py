from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Attempt


@dataclass
class ScoreResult:
    total: float
    subscores: dict[str, float]
    feedback: list[str]
    algorithm_version: str


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def evaluate_attempt(attempt: Attempt) -> ScoreResult:
    procedure = attempt.procedure
    rubric: dict[str, Any] = procedure.rubric or {}
    penalties = rubric.get("penalties", {})
    expected_time = rubric.get("expected_time_seconds", 180)

    events = list(attempt.events.all())
    forbidden_hits = sum(
        1
        for event in events
        if event.event_type == "hit" and event.payload.get("zone") == "forbidden"
    )
    target_hits = sum(
        1
        for event in events
        if event.event_type == "hit" and event.payload.get("zone") == "target"
    )
    wrong_actions = sum(1 for event in events if event.event_type == "error")

    completed_steps = {
        event.payload.get("step_id")
        for event in events
        if event.event_type == "step_completed"
    }
    total_steps = max(len(procedure.steps), 1)
    steps_completed_count = len([step for step in procedure.steps if step.get("id") in completed_steps])
    steps_omitted = max(total_steps - steps_completed_count, 0)

    duration_seconds = attempt.duration_seconds or 0
    time_over = max(duration_seconds - expected_time, 0)

    total_penalty = 0
    total_penalty += forbidden_hits * penalties.get("forbidden_hit", 6)
    total_penalty += wrong_actions * penalties.get("wrong_action", 4)
    total_penalty += steps_omitted * penalties.get("step_omitted", 5)
    total_penalty += (time_over / 10) * penalties.get("time_over", 1)

    total_score = _clamp(100 - total_penalty)

    precision = _clamp(100 - forbidden_hits * 10 - wrong_actions * 5)
    efficiency = _clamp(100 - (time_over / expected_time) * 50)
    safety = _clamp(100 - forbidden_hits * 15)
    protocol = _clamp(100 - (steps_omitted / total_steps) * 100)

    feedback: list[str] = []
    if forbidden_hits:
        feedback.append("Evita ingresar en la zona prohibida para proteger al paciente.")
    if steps_omitted:
        feedback.append("Completa todos los pasos del protocolo antes de finalizar el intento.")
    if wrong_actions:
        feedback.append("Revisa los instrumentos y la acción correcta antes de ejecutarla.")
    if time_over:
        feedback.append("Optimiza tus movimientos para reducir el tiempo total del procedimiento.")
    if target_hits == 0:
        feedback.append("Asegura contacto con la zona objetivo para mejorar la precisión.")
    if not feedback:
        feedback.append("Excelente trabajo: desempeño consistente en precisión y seguridad.")

    return ScoreResult(
        total=total_score,
        subscores={
            "precision": precision,
            "efficiency": efficiency,
            "safety": safety,
            "protocol_adherence": protocol,
        },
        feedback=feedback[:8],
        algorithm_version=rubric.get("version", "v1"),
    )
