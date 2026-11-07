"""Resend transport checks without a database or external delivery."""

import io
import json

from labsync import followup


def test_resend_sends_explicit_user_agent_and_idempotency_key(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("LABSYNC_EMAIL_FROM", "Demo <onboarding@resend.dev>")
    payload = {"to": ["recipient@example.test"], "text": "Test follow-up"}

    def provider(request, timeout):
        # Resend's edge rejects requests without a recognized User-Agent (1010).
        assert request.get_header("User-agent") == "MeetingMemory/0.1"
        assert request.get_header("Authorization") == "Bearer test-key"
        assert request.get_header("Idempotency-key") == "task-recipient-key"
        assert request.full_url == "https://api.resend.com/emails"
        assert json.loads(request.data) == payload
        assert timeout == 10
        return io.BytesIO(b'{"id":"accepted-email"}')

    monkeypatch.setattr(followup, "urlopen", provider)
    assert (
        followup.ResendEmail().send("task-recipient-key", payload) == "accepted-email"
    )
