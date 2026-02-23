from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from pip_search.internal.challenge_solvers import (
    ChallengeContext,
    ChallengeResponseBuilder,
    FastlyChallengeUnsolvable,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class StubPATProvider:
    def solve(self, *, context: ChallengeContext) -> dict[str, object]:
        return {"ty": "pat", "auth": f"auth-{context.token}"}


class StubPoWProvider:
    def solve(self, challenge: Mapping[str, Any]) -> dict[str, object]:
        return {
            "ty": "pow",
            "base": "b",
            "answer": "ab",
            "hmac": "h",
            "expires": "e",
        }


class StubMetricsProvider:
    def solve(self) -> dict[str, object]:
        return {"ty": "clientmetrics", "browser_metrics": {"client_data": "{}"}}


def test_response_builder_builds_supported_challenge_types() -> None:
    builder = ChallengeResponseBuilder(
        pat_provider=StubPATProvider(),
        pow_provider=StubPoWProvider(),
        metrics_provider=StubMetricsProvider(),
    )

    responses = builder.build(
        [{"ty": "pat"}, {"ty": "pow", "data": {}}, {"ty": "clientmetrics"}],
        context=ChallengeContext(token="token-1", path="/_fs-ch-x", referer_url="https://pypi.org"),
    )

    assert [response["ty"] for response in responses] == ["pat", "pow", "clientmetrics"]


def test_response_builder_ignores_unknown_challenges() -> None:
    builder = ChallengeResponseBuilder(
        pat_provider=StubPATProvider(),
        pow_provider=StubPoWProvider(),
        metrics_provider=StubMetricsProvider(),
    )

    responses = builder.build(
        [{"ty": "unknown"}],
        context=ChallengeContext(token="token-1", path="/_fs-ch-x", referer_url="https://pypi.org"),
    )

    assert responses == []


def test_response_builder_raises_for_captcha() -> None:
    builder = ChallengeResponseBuilder(
        pat_provider=StubPATProvider(),
        pow_provider=StubPoWProvider(),
        metrics_provider=StubMetricsProvider(),
    )

    with pytest.raises(FastlyChallengeUnsolvable, match="CAPTCHA"):
        builder.build(
            [{"ty": "captcha"}],
            context=ChallengeContext(
                token="token-1",
                path="/_fs-ch-x",
                referer_url="https://pypi.org",
            ),
        )
