"""Shared types for Fastly challenge solving."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Protocol

type ChallengeData = Mapping[str, Any]
type ChallengeResponse = dict[str, Any]


class ChallengeType(StrEnum):
    """Known Fastly challenge step types."""

    PAT = auto()
    POW = auto()
    CAPTCHA = auto()
    CLIENT_METRICS = "clientmetrics"


@dataclass(frozen=True, slots=True)
class ChallengeConfig:
    """Challenge configuration extracted from Fastly script."""

    challenges: list[ChallengeData]
    token: str
    path: str


@dataclass(frozen=True, slots=True)
class ChallengeContext:
    """Per-round context used by challenge response providers."""

    token: str
    path: str
    referer_url: str


class FingerprintProvider(Protocol):
    """Provider for sealed browser fingerprint payload."""

    def load(self) -> Mapping[str, Any]:
        """Return fingerprint payload."""


class PATProvider(Protocol):
    """Provider that resolves PAT challenge responses."""

    def solve(self, *, context: ChallengeContext) -> ChallengeResponse:
        """Build a PAT challenge response payload."""


class PoWProvider(Protocol):
    """Provider that resolves PoW challenge responses."""

    def solve(self, challenge: ChallengeData) -> ChallengeResponse:
        """Build a PoW challenge response payload."""


class MetricsProvider(Protocol):
    """Provider that resolves client metrics challenge responses."""

    def solve(self) -> ChallengeResponse:
        """Build a client metrics challenge response payload."""


class ChallengeRoundHandler(Protocol):
    """Component that builds challenge responses for a single round."""

    def build(
        self,
        challenges: list[ChallengeData],
        *,
        context: ChallengeContext,
    ) -> list[ChallengeResponse]:
        """Build challenge round responses."""
