from __future__ import annotations

import json

from pip_search.internal.challenge_solvers import ChallengeContext
from pip_search.internal.challenge_solvers.metrics import ClientMetricsChallengeProvider
from pip_search.internal.challenge_solvers.pat import PATChallengeProvider


class StubFingerprintProvider:
    def load(self) -> dict[str, object]:
        return {"userAgent": {"value": "Custom UA"}}


def test_pat_provider_returns_auth(mocker) -> None:
    client = mocker.Mock()
    client.post.return_value = mocker.Mock(
        status_code=200, json=mocker.Mock(return_value={"auth": "abc"})
    )
    provider = PATChallengeProvider(client, base_url="https://pypi.org")

    result = provider.solve(
        context=ChallengeContext(
            token="token-1",
            path="/_fs-ch-x",
            referer_url="https://pypi.org/search/",
        )
    )

    assert result == {"ty": "pat", "auth": "abc"}


def test_pat_provider_returns_empty_auth_on_http_error(mocker) -> None:
    client = mocker.Mock()
    client.post.return_value = mocker.Mock(status_code=401)
    provider = PATChallengeProvider(client, base_url="https://pypi.org")

    result = provider.solve(
        context=ChallengeContext(
            token="token-1",
            path="/_fs-ch-x",
            referer_url="https://pypi.org/search/",
        )
    )

    assert result == {"ty": "pat", "auth": ""}


def test_client_metrics_provider_uses_fingerprint_provider() -> None:
    provider = ClientMetricsChallengeProvider(fingerprint_provider=StubFingerprintProvider())

    result = provider.solve()

    assert result["ty"] == "clientmetrics"
    fingerprint_payload = json.loads(result["browser_metrics"]["client_data"])
    assert fingerprint_payload["userAgent"]["value"] == "Custom UA"
