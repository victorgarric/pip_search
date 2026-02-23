from __future__ import annotations

import pytest

from pip_search.internal.challenge_solvers import (
    ChallengeConfig,
    FastlyChallengeParseError,
    extract_script_url,
    has_challenge,
    parse_challenge_script,
)


def test_has_challenge_marker() -> None:
    html = '<script src="/_fs-ch-abc123/script.js"></script>'

    assert has_challenge(html)


def test_extract_script_url() -> None:
    html = '<link href="/_fs-ch-abc123/assets/styles.css" rel="stylesheet">'

    result = extract_script_url(html, base_url="https://pypi.org")

    assert result == "https://pypi.org/_fs-ch-abc123/script.js?reload=true"


def test_extract_script_url_raises_when_missing() -> None:
    with pytest.raises(FastlyChallengeParseError, match="Could not find challenge ID"):
        extract_script_url("<html>no challenge</html>", base_url="https://pypi.org")


def test_parse_challenge_script() -> None:
    script = 'init([{"ty":"pat"}], "token-1", "/_fs-ch-test", true);'

    result = parse_challenge_script(script)

    assert isinstance(result, ChallengeConfig)
    assert result.token == "token-1"
    assert result.path == "/_fs-ch-test"
    assert result.challenges == [{"ty": "pat"}]


def test_parse_challenge_script_invalid_payload() -> None:
    script = 'init([invalid], "token-1", "/_fs-ch-test", true);'

    with pytest.raises(FastlyChallengeParseError, match="Challenge JSON parse failed"):
        parse_challenge_script(script)


def test_parse_challenge_script_non_object_entry() -> None:
    script = 'init([{"ty":"pat"}, 1], "token-1", "/_fs-ch-test", true);'

    with pytest.raises(FastlyChallengeParseError, match="non-object entries"):
        parse_challenge_script(script)
