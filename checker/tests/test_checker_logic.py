import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import checker.app as checker_app


def test_target_display_name_http():
    assert checker_app.target_display_name("http", "http://example.com:8080/path") == "example.com:8080"


def test_target_display_name_non_http():
    assert checker_app.target_display_name("tcp", "127.0.0.1:22") == "127.0.0.1:22"


def test_check_with_retries_success_on_second_attempt(monkeypatch):
    calls = {"count": 0}

    def fake_run_single_check(_ctype, _target, _timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return (0, -1.0)
        return (1, 42.0)

    monkeypatch.setattr(checker_app, "run_single_check", fake_run_single_check)
    up, latency = checker_app.check_with_retries("http", "http://x", 2, 3)

    assert up == 1
    assert latency == 42.0
    assert calls["count"] == 2


def test_check_with_retries_all_fail(monkeypatch):
    calls = {"count": 0}

    def fake_run_single_check(_ctype, _target, _timeout):
        calls["count"] += 1
        return (0, -1.0)

    monkeypatch.setattr(checker_app, "run_single_check", fake_run_single_check)
    up, latency = checker_app.check_with_retries("http", "http://x", 2, 2)

    assert up == 0
    assert latency == -1.0
    assert calls["count"] == 2
