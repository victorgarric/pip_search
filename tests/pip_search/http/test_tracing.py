from __future__ import annotations

from pip_search.http.tracing import Redactor, body_preview


def test_redactor_redacts_sensitive_headers() -> None:
    redactor = Redactor({"authorization"})

    result = redactor.redact({"Authorization": "secret", "X-Test": "ok"})

    assert result == {"Authorization": "<redacted>", "X-Test": "ok"}


def test_body_preview_truncates_when_limit_is_hit() -> None:
    preview = body_preview("abcdef", truncate_len=3)

    assert preview == "abc…<truncated>"
