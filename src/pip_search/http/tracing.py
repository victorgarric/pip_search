from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from typing import Any


class Redactor:
    def __init__(self, sensitive_headers: AbstractSet[str]):
        self._sensitive_headers = sensitive_headers

    def redact(self, headers: Mapping[str, Any] | None) -> dict[str, str]:
        if not headers:
            return {}
        out: dict[str, str] = {}
        for k, v in headers.items():
            out[k] = "<redacted>" if k.lower() in self._sensitive_headers else v
        return out


def body_preview(body: Any, truncate_len: int = 4000) -> str:
    if truncate_len < 0:
        raise ValueError(f"truncate_len cannot be < 0: {truncate_len}")
    if isinstance(body, (bytes, bytearray)):
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            return f"<{type(body).__name__} {len(body)} bytes>"
    else:
        text = str(body)
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    return (
        (text[:truncate_len] + "…<truncated>" if len(text) > truncate_len else "")
        if truncate_len > 0
        else text
    )
