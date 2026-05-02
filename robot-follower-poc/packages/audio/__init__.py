"""Microphone capture, command recognition, and TTS hooks."""

from audio.command_catalog import AUDIO_COMMANDS, AudioCommandHelp
from audio.command_recognizer import CommandRecognizerProtocol, ConsoleCommandRecognizer
from audio.microphone import MicrophoneStream
from audio.tts import NullTextToSpeech, TextToSpeechProtocol

__all__ = [
    "AUDIO_COMMANDS",
    "AudioCommandHelp",
    "CommandRecognizerProtocol",
    "ConsoleCommandRecognizer",
    "MicrophoneStream",
    "NullTextToSpeech",
    "TextToSpeechProtocol",
]
