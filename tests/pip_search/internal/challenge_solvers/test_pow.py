from __future__ import annotations

import hashlib

import pytest

from pip_search.internal.challenge_solvers import (
    FastlyChallengeError,
    FastlyChallengeParseError,
    FastlyChallengeUnsolvable,
    PoWChallenge,
    PoWChallengeProvider,
)


def test_pow_parse_and_solve_suffix() -> None:
    provider = PoWChallengeProvider()
    base = "seed"
    answer = "ab"
    target_hash = hashlib.sha256((base + answer).encode()).hexdigest()

    parsed = provider.parse(
        {
            "base": base,
            "hash": target_hash,
            "hmac": "hmac-1",
            "expires": "12345",
            "len": 2,
        }
    )

    assert isinstance(parsed, PoWChallenge)
    assert provider.solve_suffix(parsed) == answer


def test_pow_solve_returns_response_payload() -> None:
    provider = PoWChallengeProvider()
    base = "seed"
    answer = "xy"
    target_hash = hashlib.sha256((base + answer).encode()).hexdigest()

    response = provider.solve(
        {
            "ty": "pow",
            "data": {
                "base": base,
                "hash": target_hash,
                "hmac": "hmac-2",
                "expires": "98765",
                "len": 2,
            },
        }
    )

    assert response["ty"] == "pow"
    assert response["answer"] == answer


def test_pow_parse_raises_for_missing_field() -> None:
    provider = PoWChallengeProvider()

    with pytest.raises(FastlyChallengeParseError, match="Missing/invalid PoW field"):
        provider.parse({"base": "x", "hmac": "y", "expires": "z"})


def test_pow_parse_raises_for_large_suffix() -> None:
    provider = PoWChallengeProvider()

    with pytest.raises(FastlyChallengeUnsolvable, match="suffix length too large"):
        provider.parse(
            {
                "base": "x",
                "hash": "deadbeef",
                "hmac": "y",
                "expires": "z",
                "len": 5,
            }
        )


def test_pow_unsolved_raises_error() -> None:
    provider = PoWChallengeProvider()

    challenge = PoWChallenge(
        base="seed",
        target_hash="0" * 64,
        hmac="hmac",
        expires="123",
        suffix_len=1,
    )

    with pytest.raises(FastlyChallengeError, match="PoW solution not found"):
        provider.solve_suffix(challenge)
