from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from simulator.models import Attempt, Event, Procedure
from simulator.scoring import evaluate_attempt


class ScoringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="Pass123!", role="STUDENT")
        self.procedure = Procedure.objects.create(
            name="Test",
            specialty="General",
            difficulty="Básica",
            procedure_type="Abierta",
            duration_estimated_minutes=10,
            description="Test",
            steps=[
                {"id": 1, "title": "Step 1", "instruments": ["SCALPEL"], "actions": ["CUT"]},
                {"id": 2, "title": "Step 2", "instruments": ["FORCEPS"], "actions": ["GRAB"]},
            ],
            instruments=[{"name": "Bisturí", "tool": "SCALPEL"}],
            zones={
                "target": {"x": 0.3, "y": 1.2, "z": 0.3, "radius": 0.3},
                "forbidden": {"x": -0.3, "y": 1.1, "z": 0.2, "radius": 0.3},
            },
            checklist=[{"code": "C1", "label": "Checklist"}],
            rubric={
                "version": "rules_v2",
                "expected_time_seconds": 120,
                "penalties": {
                    "forbidden_hit": 10,
                    "wrong_action": 5,
                    "step_omitted": 10,
                    "time_over": 1,
                    "wrong_instrument": 4,
                    "erratic_move": 1,
                },
            },
            prompt_base="Prompt base",
            is_playable=True,
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

    def test_scoring_perfect(self):
        Event.objects.create(attempt=self.attempt, event_type="step_completed", payload={"step_id": 1}, timestamp_ms=100)
        Event.objects.create(attempt=self.attempt, event_type="step_completed", payload={"step_id": 2}, timestamp_ms=200)
        result = evaluate_attempt(self.attempt)
        self.assertGreaterEqual(result.total, 90)

    def test_scoring_missing_steps(self):
        Event.objects.create(attempt=self.attempt, event_type="step_completed", payload={"step_id": 1}, timestamp_ms=100)
        result = evaluate_attempt(self.attempt)
        self.assertLess(result.subscores["protocol_adherence"], 100)


class ReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="student", password="Pass123!", role="STUDENT")
        self.client.force_authenticate(self.user)
        self.procedure = Procedure.objects.create(
            name="Report Test",
            specialty="General",
            difficulty="Básica",
            procedure_type="Abierta",
            duration_estimated_minutes=10,
            description="Test",
            steps=[{"id": 1, "title": "Step 1", "instruments": ["SCALPEL"], "actions": ["CUT"]}],
            instruments=[{"name": "Bisturí", "tool": "SCALPEL"}],
            zones={"target": {"x": 0.3, "y": 1.2, "z": 0.3, "radius": 0.3}, "forbidden": {"x": -0.3, "y": 1.1, "z": 0.2, "radius": 0.3}},
            checklist=[{"code": "C1", "label": "Checklist"}],
            rubric={"version": "rules_v2", "expected_time_seconds": 120, "penalties": {}},
            prompt_base="Prompt",
            is_playable=True,
        )
        self.attempt = Attempt.objects.create(user=self.user, procedure=self.procedure, duration_seconds=100)

    def test_pdf_report(self):
        response = self.client.get(f"/api/reports/{self.attempt.id}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/pdf"))
