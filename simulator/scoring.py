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
    breakdown: dict[str, Any]


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def evaluate_attempt(attempt: Attempt) -> ScoreResult:
    procedure = attempt.procedure
    rubric: dict[str, Any] = procedure.rubric or {}
    penalties = rubric.get("penalties", {})
    expected_time = rubric.get("expected_time_seconds", 180)

    events = list(attempt.events.all().order_by("timestamp_ms"))
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
    forbidden_contact_ms = sum(
        event.payload.get("duration_ms", 0)
        for event in events
        if event.event_type == "contact_duration" and event.payload.get("zone") == "forbidden"
    )
    forceful_actions = sum(
        1
        for event in events
        if event.event_type == "action" and event.payload.get("intensity", 0) >= 8
    )

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

    tool_selects = [event for event in events if event.event_type == "tool_select"]
    actions = [event for event in events if event.event_type == "action"]
    move_events = [event for event in events if event.event_type == "move"]
    current_tool = tool_selects[-1].payload.get("tool") if tool_selects else None
    wrong_instrument = 0
    for event in actions:
        expected_tools = _expected_tools_for_step(procedure.steps, completed_steps)
        tool_used = event.payload.get("tool") or current_tool
        if expected_tools and tool_used not in expected_tools:
            wrong_instrument += 1
        current_tool = tool_used or current_tool

    erratic_moves = max(len(move_events) - (duration_seconds * 6), 0)

    total_penalty = 0
    total_penalty += forbidden_hits * penalties.get("forbidden_hit", 6)
    total_penalty += wrong_actions * penalties.get("wrong_action", 4)
    total_penalty += steps_omitted * penalties.get("step_omitted", 5)
    total_penalty += (time_over / 10) * penalties.get("time_over", 1)
    total_penalty += wrong_instrument * penalties.get("wrong_instrument", 4)
    total_penalty += (erratic_moves / 10) * penalties.get("erratic_move", 1)
    total_penalty += (forbidden_contact_ms / 1000) * penalties.get("forbidden_contact", 2)
    total_penalty += forceful_actions * penalties.get("forceful_action", 2)

    total_score = _clamp(100 - total_penalty)

    precision = _clamp(100 - forbidden_hits * 10 - wrong_actions * 5)
    efficiency = _clamp(100 - (time_over / expected_time) * 50)
    safety = _clamp(100 - forbidden_hits * 15 - (forbidden_contact_ms / 1000) * 2)
    protocol = _clamp(100 - (steps_omitted / total_steps) * 100)
    instrument_handling = _clamp(100 - wrong_instrument * 12 - (erratic_moves / 10))

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
    if wrong_instrument:
        feedback.append("Selecciona el instrumento adecuado para cada paso antes de ejecutar acciones.")
    if forbidden_contact_ms:
        feedback.append("Reduce el tiempo de contacto en zonas prohibidas para mantener seguridad.")
    if forceful_actions:
        feedback.append("Modera la intensidad de las acciones para evitar trauma tisular.")
    if erratic_moves:
        feedback.append("Reduce movimientos erráticos para mejorar la estabilidad manual.")
    if not feedback:
        feedback.append("Excelente trabajo: desempeño consistente en precisión y seguridad.")

    return ScoreResult(
        total=total_score,
        subscores={
            "precision": precision,
            "efficiency": efficiency,
            "safety": safety,
            "protocol_adherence": protocol,
            "instrument_handling": instrument_handling,
        },
        feedback=feedback[:8],
        algorithm_version=rubric.get("version", "rules_v2"),
        breakdown={
            "forbidden_hits": forbidden_hits,
            "target_hits": target_hits,
            "wrong_actions": wrong_actions,
            "forbidden_contact_ms": forbidden_contact_ms,
            "forceful_actions": forceful_actions,
            "steps_omitted": steps_omitted,
            "time_over_seconds": time_over,
            "wrong_instrument": wrong_instrument,
            "erratic_moves": erratic_moves,
        },
    )


def _expected_tools_for_step(steps: list[dict[str, Any]], completed_steps: set[int]) -> list[str]:
    pending_steps = [step for step in steps if step.get("id") not in completed_steps]
    if not pending_steps:
        return []
    return pending_steps[0].get("instruments", [])
