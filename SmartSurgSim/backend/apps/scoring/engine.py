from collections import Counter


ALGO_VERSION = 'rules_v1'


def evaluate_attempt(attempt, procedure):
    events = list(attempt.events.order_by('t_ms'))
    rubric = procedure.rubric or {}
    steps = procedure.steps or []
    step_actions = {step.get('id'): step.get('action') for step in steps}
    step_sequence = [step.get('id') for step in steps]

    errors = []
    hits_prohibited = 0
    hits_objective = 0
    action_errors = 0
    completed_steps = []

    current_step_index = 0
    for event in events:
        if event.event_type == 'hit':
            zone = event.payload.get('zone')
            if zone == 'prohibited':
                hits_prohibited += 1
            elif zone == 'objective':
                hits_objective += 1
        if event.event_type == 'action':
            action = event.payload.get('name')
            if current_step_index < len(step_sequence):
                expected_step_id = step_sequence[current_step_index]
                expected_action = step_actions.get(expected_step_id)
                if action == expected_action:
                    completed_steps.append(expected_step_id)
                    current_step_index += 1
                else:
                    action_errors += 1
                    errors.append('acción incorrecta')
        if event.event_type == 'step_completed':
            step_id = event.payload.get('step_id')
            if step_id and step_id in step_sequence and step_id not in completed_steps:
                completed_steps.append(step_id)
                if current_step_index < len(step_sequence) and step_sequence[current_step_index] == step_id:
                    current_step_index += 1
        if event.event_type == 'error':
            errors.append(event.payload.get('code', 'error'))

    omitted_steps = [step for step in step_sequence if step not in completed_steps]

    duration_ms = attempt.duration_ms or 0
    target_time_ms = rubric.get('target_time_ms', 60000)
    time_penalty = max(0, duration_ms - target_time_ms) / max(target_time_ms, 1)

    precision = max(0, 100 - (hits_objective * 0.5) - (hits_prohibited * 5))
    safety = max(0, 100 - hits_prohibited * 12)
    protocol_adherence = max(0, 100 - (len(omitted_steps) * 10) - (action_errors * 5))
    efficiency = max(0, 100 - (time_penalty * 30) - (len(events) * 0.05))

    total = round((precision + safety + protocol_adherence + efficiency) / 4)

    feedback = []
    if hits_prohibited == 0:
        feedback.append('Buena seguridad: evitaste zonas prohibidas.')
    else:
        feedback.append('Evita las zonas prohibidas para reducir riesgos.')
    if omitted_steps:
        feedback.append('Completa todos los pasos del protocolo sin omisiones.')
    else:
        feedback.append('Excelente adherencia al protocolo.')
    if action_errors > 0:
        feedback.append('Revisa el orden de acciones y los instrumentos sugeridos.')
    if duration_ms > target_time_ms:
        feedback.append('Optimiza tu tiempo para mejorar eficiencia.')
    if hits_objective > 0:
        feedback.append('Mejora la precisión dentro de la zona objetivo.')

    result = {
        'score_total': int(max(0, min(100, total))),
        'subscores': {
            'precision': int(max(0, min(100, precision))),
            'efficiency': int(max(0, min(100, efficiency))),
            'safety': int(max(0, min(100, safety))),
            'protocol_adherence': int(max(0, min(100, protocol_adherence))),
        },
        'feedback': '\n'.join(f"- {item}" for item in feedback[:8]),
        'algo_version': ALGO_VERSION,
        'stats': {
            'hits_prohibited': hits_prohibited,
            'hits_objective': hits_objective,
            'action_errors': action_errors,
            'omitted_steps': omitted_steps,
            'completed_steps': completed_steps,
        },
    }
    return result
