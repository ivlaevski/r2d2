"""Human-readable list of supported local audio / console commands (single source of truth)."""

from __future__ import annotations

from typing import TypedDict


class AudioCommandHelp(TypedDict):
    """One entry for dashboards and docs."""

    phrase: str
    description: str


AUDIO_COMMANDS: list[AudioCommandHelp] = [
    {
        "phrase": "FOLLOW",
        "description": "Enter follow mode (track person when perception reports a target).",
    },
    {"phrase": "STAY", "description": "Hold position / stop following until changed."},
    {"phrase": "STOP", "description": "Emergency stop (latched until RESET)."},
    {"phrase": "EMERGENCY_STOP", "description": "Same effect as STOP."},
    {"phrase": "RESET", "description": "Clear emergency latch and return to IDLE."},
    {
        "phrase": "CHANGE_DISTANCE 2.0",
        "description": "Set desired follow distance in meters (replace 2.0).",
    },
    {
        "phrase": "come closer / closer",
        "description": "Nudge follow distance closer (voice + ElevenLabs).",
    },
    {
        "phrase": "move back / back up / further away",
        "description": "Nudge follow distance farther.",
    },
    {
        "phrase": "slower / slow down",
        "description": "Increase follow distance slightly (PoC = slower approach).",
    },
    {
        "phrase": "faster / speed up",
        "description": "Decrease follow distance slightly (PoC = snappier).",
    },
    {
        "phrase": "natural language (ElevenLabs)",
        "description": (
            "With ELEVENLABS_AUDIO_ENABLED, transcripts are parsed locally "
            "for the same intents."
        ),
    },
]
