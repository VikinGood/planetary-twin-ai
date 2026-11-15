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


# --- Numbers written in words -------------------------------------------------------------
# The model sometimes writes "minus twenty-eight point six degrees" instead of "-28.6", which
# the digit regex cannot check. words_to_digits() rewrites those phrases with digits, so the
# checker sees every number and the text reads consistently. Standalone "one" is left alone
# ("one of the sites").

_UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                      "thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
_FRACTIONS = {"half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4, "fifth": 5, "sixth": 6,
              "sixths": 6, "eighth": 8, "tenth": 10}
_NUM_WORD = "|".join(sorted(list(_UNITS) + list(_TENS) + ["hundred", "thousand", "point", "minus"], key=len, reverse=True))
_SEP = r"[\s\-\u2010\u2011\u2012\u2013]+"
_PHRASE_RE = re.compile(rf"\b(?:{_NUM_WORD})(?:{_SEP}(?:{_NUM_WORD}|and))*\b(?:{_SEP}(?:{'|'.join(_FRACTIONS)})\b)?", re.IGNORECASE)


def _phrase_value(words: list[str]) -> str | None:
    sign = ""
    if words and words[0] == "minus":
        sign, words = "-", words[1:]
    if not words:
        return None
    if words[-1] in _FRACTIONS:
        num = _phrase_value(words[:-1])
        return None if num is None else f"{sign}{num}/{_FRACTIONS[words[-1]]}"
    decimals = ""
    if "point" in words:
        i = words.index("point")
        digits = words[i + 1:]
        if not digits or any(d not in _UNITS or _UNITS[d] > 9 for d in digits):
            return None
        decimals = "." + "".join(str(_UNITS[d]) for d in digits)
        words = words[:i]
    total = current = 0
    seen = False
    for w in words:
        if w == "and":
            continue
        if w in _UNITS:
            current += _UNITS[w]
        elif w in _TENS:
            current += _TENS[w]
        elif w == "hundred":
            current = max(current, 1) * 100
        elif w == "thousand":
            total += max(current, 1) * 1000
            current = 0
        else:
            return None
        seen = True
    if not seen and not decimals:
        return None
    return f"{sign}{total + current}{decimals}"


def words_to_digits(text: str) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(0)
        words = [w.lower() for w in re.split(_SEP, raw) if w]
        while words and words[-1] in ("and", "point", "minus"):
            words.pop()
        if words in (["one"], []):
            return raw
        value = _phrase_value(words)
        if value is None:
            return raw
        # keep a trailing separator such as the hyphen in "fourteen-day"
        tail = raw[len(raw.rstrip("-\u2010\u2011\u2012\u2013 ")):]
        return value + tail
    return _PHRASE_RE.sub(repl, text or "")


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
    allowed: set[float] = set(float(i) for i in range(13))  # small counts ("four characteristics")
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
    for n in numbers_in_text(words_to_digits(_text_of(interp))):
        if not any(abs(n - a) <= tolerance for a in allowed):
            bad.append(n)
    return bad
