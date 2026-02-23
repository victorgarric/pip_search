"""Challenge response state machine."""

from __future__ import annotations

from loguru import logger

from .errors import FastlyChallengeUnsolvable
from .types import (
    ChallengeContext,
    ChallengeData,
    ChallengeResponse,
    ChallengeType,
    MetricsProvider,
    PATProvider,
    PoWProvider,
)


class ChallengeResponseBuilder:
    """Build challenge response payloads for one challenge round."""

    def __init__(
        self,
        *,
        pat_provider: PATProvider,
        pow_provider: PoWProvider,
        metrics_provider: MetricsProvider,
    ) -> None:
        self._pat_provider = pat_provider
        self._pow_provider = pow_provider
        self._metrics_provider = metrics_provider

    def build(
        self,
        challenges: list[ChallengeData],
        *,
        context: ChallengeContext,
    ) -> list[ChallengeResponse]:
        """Build response payload list for a Fastly challenge round."""
        responses: list[ChallengeResponse] = []

        for challenge in challenges:
            challenge_type = str(challenge.get("ty", ""))

            match challenge_type:
                case ChallengeType.PAT:
                    responses.append(self._pat_provider.solve(context=context))

                case ChallengeType.POW:
                    responses.append(self._pow_provider.solve(challenge))

                case ChallengeType.CLIENT_METRICS:
                    responses.append(self._metrics_provider.solve())

                case ChallengeType.CAPTCHA:
                    raise FastlyChallengeUnsolvable("CAPTCHA challenge cannot be solved")

                case _:
                    logger.debug("Fastly: ignoring unknown challenge type: {}", challenge_type)

        return responses
