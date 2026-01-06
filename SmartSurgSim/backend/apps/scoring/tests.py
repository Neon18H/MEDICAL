from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.procedures.models import Procedure
from apps.simulation.models import Attempt, Event
from .engine import evaluate_attempt


class ScoringEngineTests(TestCase):
    def test_scoring_basic(self):
        User = get_user_model()
        user = User.objects.create_user(username='tester', password='Test123!')
        procedure = Procedure.objects.create(
            title='Test Proc',
            description='Desc',
            difficulty='Easy',
            steps=[{'id': 's1', 'label': 'Step', 'action': 'CUT'}],
            zones={'objective': {'shape': 'circle', 'x': 10, 'y': 10, 'radius': 5}},
            rubric={'target_time_ms': 1000},
        )
        attempt = Attempt.objects.create(user=user, procedure=procedure, duration_ms=500)
        Event.objects.create(attempt=attempt, t_ms=100, event_type='action', payload={'name': 'CUT'})
        Event.objects.create(attempt=attempt, t_ms=150, event_type='hit', payload={'zone': 'objective', 'x': 10, 'y': 10})

        result = evaluate_attempt(attempt, procedure)
        self.assertGreaterEqual(result['score_total'], 0)
        self.assertIn('precision', result['subscores'])
