from __future__ import annotations

import json

import pytest

from pip_search.internal.challenge_solvers import (
    ChallengeConfig,
    FastlyChallengeError,
    FastlyChallengeParseError,
    FastlyChallengeSolver,
)


def _response(mocker, *, status_code: int = 200, text: str = "", json_data=None):
    response = mocker.Mock()
    response.status_code = status_code
    response.text = text
    if json_data is None:
        response.json.side_effect = json.JSONDecodeError("invalid", "", 0)
    else:
        response.json.return_value = json_data
    return response


def test_ensure_access_returns_true_when_no_challenge(mocker) -> None:
    client = mocker.Mock()
    client.get.return_value = _response(mocker, status_code=200, text="<html>ok</html>")

    solver = FastlyChallengeSolver(client)

    assert solver.ensure_access("https://pypi.org/search/?q=a")


def test_ensure_access_fetches_script_and_solves_chain(mocker) -> None:
    client = mocker.Mock()
    client.get.side_effect = [
        _response(mocker, status_code=200, text='<script src="/_fs-ch-abc/script.js"></script>'),
        _response(
            mocker,
            status_code=200,
            text='init([{"ty":"pat"}], "token-1", "/_fs-ch-abc", true);',
        ),
    ]
    client.post.return_value = _response(mocker, status_code=200, json_data={"status": "success"})

    solver = FastlyChallengeSolver(client)

    assert solver.ensure_access("https://pypi.org/search/?q=a", referer="https://pypi.org/search/")
    assert client.post.call_count == 2


def test_ensure_access_raises_when_probe_fails(mocker) -> None:
    client = mocker.Mock()
    client.get.return_value = _response(mocker, status_code=403, text="forbidden")

    solver = FastlyChallengeSolver(client)

    with pytest.raises(FastlyChallengeError, match="Challenge probe failed"):
        solver.ensure_access("https://pypi.org/search/?q=a")


def test_post_back_raises_for_invalid_json(mocker) -> None:
    client = mocker.Mock()
    client.post.return_value = _response(mocker, status_code=200, json_data=None)
    solver = FastlyChallengeSolver(client)

    from pip_search.internal.challenge_solvers.types import ChallengeContext

    with pytest.raises(FastlyChallengeParseError, match="Invalid JSON"):
        solver._post_back(
            context=ChallengeContext(
                token="token-1", path="/_fs-ch-abc", referer_url="https://pypi.org"
            ),
            responses=[{"ty": "pat", "auth": ""}],
        )


def test_solve_challenge_chain_retries_with_next_round(mocker) -> None:
    client = mocker.Mock()

    class StubBuilder:
        def __init__(self) -> None:
            self.calls = 0

        def build(self, challenges, *, context):
            self.calls += 1
            if self.calls == 1:
                assert challenges == [{"ty": "pat"}]
                assert context.token == "token-1"
                return [{"ty": "pat", "auth": ""}]
            assert challenges == [{"ty": "pow", "data": {}}]
            assert context.token == "token-2"
            return [{"ty": "pow", "answer": "ab", "base": "b", "hmac": "h", "expires": "e"}]

    client.post.side_effect = [
        _response(
            mocker,
            status_code=200,
            json_data={"status": "", "ch": [{"ty": "pow", "data": {}}], "tok": "token-2"},
        ),
        _response(mocker, status_code=200, json_data={"status": "success"}),
    ]

    solver = FastlyChallengeSolver(client, response_builder=StubBuilder())

    assert solver._solve_challenge_chain(
        ChallengeConfig(challenges=[{"ty": "pat"}], token="token-1", path="/_fs-ch-abc"),
        referer_url="https://pypi.org/search/",
    )
