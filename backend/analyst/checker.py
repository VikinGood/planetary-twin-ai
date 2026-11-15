"""Deterministic checker: an AI interpretation may only mention numbers that are in its input.

AI use disclosure: portions generated with AI (Claude); reviewed by the team.

Every number in the input (scores, measured values, coordinates, numbers inside strings such
as "1/6 g" or "Nobile Rim 1") becomes "allowed", together with the usual ways of writing
it: rounded to 0-3 decimals and, for values in [0, 1], as a percentage. Any other number in
the text fields of the interpretation is reported as invented.
"""

from __future__ import annotations

import math
import re

# Numbers like 12, -3.5, 0.82, 1,036 (thousands), 45% ; avoids matching inside words like "MOD11A2".
NUMBER_RE = re.compile(r"(?<![\w.])[-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.])[-−]?\d+(?:\.\d+)?(?![\w])")

TEXT_FIELDS = ("analog_summary", "non_analog_summary", "testable_activities", "characteristic_highlights", "confidence_note")


def _parse(token: str) -> float:
    return float(token.replace("−", "-").replace(",", ""))


def numbers_in_text(text: str) -> list[float]:
    return [_parse(t) for t in NUMBER_RE.findall(text or "")]


def _walk(obj):
    """Yield every number and every number found inside strings of a nested object."""
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        if math.isfinite(obj):
            yield float(obj)
    elif isinstance(obj, str):
        yield from numbers_in_text(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from numbers_in_text(str(k))
            yield from _walk(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk(v)


def allowed_numbers(result: dict) -> set[float]:
    allowed: set[float] = set()
    for x in _walk(result):
        variants = {x, abs(x)}
        for d in range(4):
            variants.add(round(x, d))
            variants.add(round(abs(x), d))
        if 0 <= x <= 1:
            for d in range(2):
                variants.add(round(x * 100, d))
        allowed |= variants
    return allowed


def _text_of(interp: dict) -> str:
    parts = []
    for f in TEXT_FIELDS:
        v = interp.get(f)
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            for item in v:
                parts.append(item if isinstance(item, str) else " ".join(str(x) for x in (item or {}).values()))
    return "\n".join(parts)


def invented_numbers(interp: dict, result: dict, tolerance: float = 1e-6) -> list[float]:
    """Return the numbers in the interpretation's text fields that are not in the input."""
    allowed = allowed_numbers(result)
    bad = []
    for n in numbers_in_text(_text_of(interp)):
        if not any(abs(n - a) <= tolerance for a in allowed):
            bad.append(n)
    return bad
