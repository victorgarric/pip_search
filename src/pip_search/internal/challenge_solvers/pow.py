"""Proof-of-Work challenge provider implementation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from typing import Any

from loguru import logger

from .errors import FastlyChallengeError, FastlyChallengeParseError, FastlyChallengeUnsolvable
from .types import ChallengeData, ChallengeResponse, ChallengeType


@dataclass(frozen=True, slots=True)
class PoWChallenge:
    """Proof-of-work challenge payload."""

    base: str
    target_hash: str
    hmac: str
    expires: str
    suffix_len: int = 2


class PoWChallengeProvider:
    """Resolve PoW challenge payloads by brute-forcing suffix."""

    _CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    def solve(self, challenge: ChallengeData) -> ChallengeResponse:
        """Return PoW challenge response payload."""
        data = challenge.get("data")
        if not isinstance(data, Mapping):
            raise FastlyChallengeParseError("Missing/invalid PoW data payload")

        parsed = self.parse(data)
        answer = self.solve_suffix(parsed)

        return {
            "ty": ChallengeType.POW,
            "base": parsed.base,
            "answer": answer,
            "hmac": parsed.hmac,
            "expires": parsed.expires,
        }

    def parse(self, data: Mapping[str, Any]) -> PoWChallenge:
        """Parse raw PoW challenge data into a strongly typed object."""

        def as_str(key: str) -> str:
            value = data.get(key)
            if not isinstance(value, str) or not value:
                raise FastlyChallengeParseError(f"Missing/invalid PoW field: {key}")
            return value

        suffix_len = 2
        for key in ("len", "length", "suffix_len"):
            value = data.get(key)
            if isinstance(value, int):
                suffix_len = value
                break
            if isinstance(value, str) and value.isdigit():
                suffix_len = int(value)
                break

        if suffix_len > 4:
            raise FastlyChallengeUnsolvable(f"PoW suffix length too large: {suffix_len}")

        return PoWChallenge(
            base=as_str("base"),
            target_hash=as_str("hash"),
            hmac=as_str("hmac"),
            expires=as_str("expires"),
            suffix_len=suffix_len,
        )

    def solve_suffix(self, challenge: PoWChallenge) -> str:
        """Find suffix that satisfies PoW target hash."""
        logger.debug(
            "Fastly: solving PoW: base_len={} suffix_len={} target_prefix={}",
            len(challenge.base),
            challenge.suffix_len,
            challenge.target_hash[:16],
        )

        for tup in product(self._CHARSET, repeat=challenge.suffix_len):
            suffix = "".join(tup)
            candidate = f"{challenge.base}{suffix}".encode("utf-8", errors="strict")
            if sha256(candidate).hexdigest() == challenge.target_hash:
                logger.debug("Fastly: PoW solution: {}", suffix)
                return suffix

        raise FastlyChallengeError("PoW solution not found")
