"""Runtime model metadata stays useful without copying private meeting content."""

import logging

import pytest

from labsync import codex_client


@pytest.mark.parametrize("fails", [False, True])
def test_model_call_logs_status_usage_and_timing_without_content(
    monkeypatch, caplog, fails
):
    def execute(*args, **kwargs):
        if fails:
            raise RuntimeError("provider failed with private detail")
        return "private response", {"input_tokens": 12, "output_tokens": 3}

    monkeypatch.setattr(codex_client, "_run", execute)
    with caplog.at_level(logging.INFO, logger="labsync.codex_client"):
        if fails:
            with pytest.raises(RuntimeError):
                codex_client.run(
                    "private transcript", {}, model="test-model", timeout=5, task="chat"
                )
        else:
            codex_client.run(
                "private transcript", {}, model="test-model", timeout=5, task="chat"
            )
    record = caplog.records[-1].getMessage()
    assert "request_id=" in record and "elapsed_seconds=" in record
    assert "model=test-model" in record and "task=chat" in record
    assert f"status={'failed' if fails else 'completed'}" in record
    assert ('"input_tokens": 12' in record) is not fails
    assert "private" not in record
