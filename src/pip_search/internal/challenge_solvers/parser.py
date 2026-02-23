"""Parsing utilities for Fastly challenge HTML/script payloads."""

from __future__ import annotations

import re
import json
from typing import Any

from .errors import FastlyChallengeParseError
from .types import ChallengeConfig

CHALLENGE_MARKER = "_fs-ch-"


def has_challenge(html: str) -> bool:
    """Return whether response body contains a Fastly challenge marker."""
    return CHALLENGE_MARKER in html


def extract_script_url(html: str, *, base_url: str) -> str:
    """Extract challenge script URL from challenge page HTML."""
    challenge_match = re.search(rf"/{CHALLENGE_MARKER}([^/\"']+)/", html)
    if not challenge_match:
        raise FastlyChallengeParseError("Could not find challenge ID in HTML")

    challenge_id = challenge_match.group(1)
    return f"{base_url.rstrip('/')}/{CHALLENGE_MARKER}{challenge_id}/script.js?reload=true"


def parse_challenge_script(script: str) -> ChallengeConfig:
    """Parse challenge script and extract initial challenge configuration."""
    init_match = re.search(
        r'init\(\s*(\[.*?\])\s*,\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']',
        script,
        re.DOTALL,
    )
    if not init_match:
        raise FastlyChallengeParseError("Could not locate init() call in script")

    array_str = init_match.group(1)
    token = init_match.group(2)
    path = init_match.group(3)

    try:
        parsed: Any = json.loads(array_str)
    except json.JSONDecodeError as exc:
        raise FastlyChallengeParseError(f"Challenge JSON parse failed: {exc}") from exc

    if not isinstance(parsed, list):
        raise FastlyChallengeParseError("Challenge JSON was not a list")

    if any(not isinstance(item, dict) for item in parsed):
        raise FastlyChallengeParseError("Challenge list contained non-object entries")

    challenges = list(parsed)
    return ChallengeConfig(challenges=challenges, token=token, path=path)
