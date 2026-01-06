from django.test import TestCase

from accounts.models import User
from simulator.models import Attempt, Event, Procedure
from simulator.scoring import evaluate_attempt


class ScoringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="Pass123!", role="STUDENT")
        self.procedure = Procedure.objects.create(
            name="Test",
            description="Test",
            steps=[{"id": 1, "title": "Step 1"}, {"id": 2, "title": "Step 2"}],
            instruments=["Tool"],
            zones={"target": {"x": 100, "y": 100, "radius": 20}, "forbidden": {"x": 200, "y": 200, "radius": 20}},
            checklist=[{"code": "C1", "label": "Checklist"}],
            rubric={
                "version": "v1",
                "expected_time_seconds": 120,
                "penalties": {"forbidden_hit": 10, "wrong_action": 5, "step_omitted": 10, "time_over": 1},
            },
        )
        self.attempt = Attempt.objects.create(user=self.user, procedure=self.procedure, duration_seconds=150)

    def test_scoring_penalties(self):
        Event.objects.create(attempt=self.attempt, event_type="hit", payload={"zone": "forbidden"}, timestamp_ms=100)
        Event.objects.create(attempt=self.attempt, event_type="step_completed", payload={"step_id": 1}, timestamp_ms=200)
        Event.objects.create(attempt=self.attempt, event_type="error", payload={"code": "WRONG_ACTION"}, timestamp_ms=250)

        result = evaluate_attempt(self.attempt)
        self.assertLess(result.total, 100)
        self.assertIn("precision", result.subscores)
        self.assertTrue(result.feedback)
