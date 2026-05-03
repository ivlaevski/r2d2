"""Microphone capture, command recognition, and TTS hooks."""

from audio.audio_backend import AudioBackend
from audio.command_catalog import AUDIO_COMMANDS, AudioCommandHelp
from audio.command_recognizer import CommandRecognizerProtocol, ConsoleCommandRecognizer
from audio.microphone import MicrophoneStream
from audio.transcript_store import TranscriptStore
from audio.tts import NullTextToSpeech, TextToSpeechProtocol

__all__ = [
    "AUDIO_COMMANDS",
    "AudioBackend",
    "AudioCommandHelp",
    "CommandRecognizerProtocol",
    "ConsoleCommandRecognizer",
    "MicrophoneStream",
    "NullTextToSpeech",
    "TextToSpeechProtocol",
    "TranscriptStore",
]
