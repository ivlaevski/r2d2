"""Parse natural-language user text into at most one local robot command."""

from __future__ import annotations

import re
from typing import Final

from contracts.audio import DetectedRobotCommand

_WORD_NUMS: Final[dict[str, float]] = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
}

_STOP_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bstop\b", re.I),
    re.compile(r"\bhalt\b", re.I),
    re.compile(r"\bemergency\s+stop\b", re.I),
    re.compile(r"\bfreeze\b", re.I),
]

_RESET_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\breset\b", re.I),
    re.compile(r"\bclear\s+emergency\b", re.I),
    re.compile(r"\bresume\s+from\s+emergency\b", re.I),
]

_FOLLOW_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bfollow\b", re.I),
    re.compile(r"\bfollow\s+me\b", re.I),
    re.compile(r"\bcome\s+with\s+me\b", re.I),
    re.compile(r"\bstart\s+following\b", re.I),
]

_STAY_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bstay\b", re.I),
    re.compile(r"\bwait\b", re.I),
    re.compile(r"\bstay\s+here\b", re.I),
    re.compile(r"\bhold\s+position\b", re.I),
]

_COME_CLOSER_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bcome\s+closer\b", re.I),
    re.compile(r"\bcloser\b", re.I),
]

_MOVE_BACK_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bmove\s+back\b", re.I),
    re.compile(r"\bback\s+up\b", re.I),
    re.compile(r"\bfurther\s+away\b", re.I),
]

_SLOWER_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bslower\b", re.I),
    re.compile(r"\bslow\s+down\b", re.I),
]

_FASTER_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bfaster\b", re.I),
    re.compile(r"\bspeed\s+up\b", re.I),
]

# Distance phrases: "change distance to 2 meters", "keep 2 m", "two meters", etc.
_RE_DECIMAL: Final[re.Pattern[str]] = re.compile(
    r"(?:to|at|keep|stay|follow(?:ing)?)\s+([0-9]+(?:\.[0-9]+)?)\s*(?:m|meter|meters)?",
    re.I,
)
_RE_WORD_DISTANCE: Final[re.Pattern[str]] = re.compile(
    r"(?:to|at|keep|stay)\s+([a-z]+)(?:\s+(?:meter|meters|m))?\b",
    re.I,
)
_RE_ONE_AND_HALF: Final[re.Pattern[str]] = re.compile(
    r"\bone\s+and\s+a\s+half\s+meters?\b",
    re.I,
)


def _normalize(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^\w\s\.]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _parse_distance_meters(snippet: str) -> float | None:
    """Extract a distance in meters from a substring, or None."""

    s = snippet.strip()
    m0 = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:m|meter|meters)?\b", s, re.I)
    if m0:
        return float(m0.group(1))
    m = _RE_DECIMAL.search(s)
    if m:
        return float(m.group(1))
    m2 = _RE_ONE_AND_HALF.search(s)
    if m2:
        return 1.5
    m3 = _RE_WORD_DISTANCE.search(s)
    if m3:
        w = m3.group(1).lower()
        if w in _WORD_NUMS:
            return float(_WORD_NUMS[w])
    # "two meters" at end
    for word, val in _WORD_NUMS.items():
        if re.search(rf"\b{word}\s+meters?\b", s, re.I):
            return float(val)
    return None


def _change_distance_from_text(norm: str, raw: str) -> DetectedRobotCommand | None:
    patterns = [
        re.compile(r"change\s+distance\s+to\s+(.+)$", re.I),
        re.compile(r"keep\s+(.+)$", re.I),
        re.compile(r"stay\s+(.+)$", re.I),
        re.compile(r"follow\s+at\s+(.+)$", re.I),
    ]
    for pat in patterns:
        m = pat.search(norm)
        if m:
            dist = _parse_distance_meters(m.group(1))
            if dist is not None:
                return DetectedRobotCommand(
                    command="CHANGE_DISTANCE",
                    distance_m=dist,
                    raw_text=raw,
                    confidence=1.0,
                )
    return None


def parse_robot_command_from_transcript(text: str) -> DetectedRobotCommand | None:
    """
    Return at most one command, prioritizing STOP over everything else.

    Normalizes case and strips most punctuation before matching.
    """

    raw = text.strip()
    if not raw:
        return None
    norm = _normalize(raw)

    for pat in _STOP_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="STOP", raw_text=raw, confidence=1.0)

    for pat in _RESET_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="RESET", raw_text=raw, confidence=1.0)

    cd = _change_distance_from_text(norm, raw)
    if cd is not None:
        return cd

    for pat in _STAY_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="STAY", raw_text=raw, confidence=1.0)

    for pat in _FOLLOW_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="FOLLOW", raw_text=raw, confidence=1.0)

    for pat in _COME_CLOSER_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="COME_CLOSER", raw_text=raw, confidence=1.0)

    for pat in _MOVE_BACK_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="MOVE_BACK", raw_text=raw, confidence=1.0)

    for pat in _SLOWER_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="SLOWER", raw_text=raw, confidence=1.0)

    for pat in _FASTER_PATTERNS:
        if pat.search(norm):
            return DetectedRobotCommand(command="FASTER", raw_text=raw, confidence=1.0)

    return None
