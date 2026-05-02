"""Console command ingress; optionally forwards commands to the HTTP API."""

from __future__ import annotations

import sys
import threading
import time

import httpx
from dotenv import load_dotenv

from audio.command_recognizer import parse_command_line
from infrastructure.config import Settings
from infrastructure.logging import configure_logging, get_logger

_LOG = get_logger(__name__)

_HEARTBEAT_S = 8.0


def _post_listening(client: httpx.Client, base: str, listening: bool) -> None:
    client.post(f"{base}/audio/listening", json={"listening": listening}, timeout=5.0)


def main() -> None:
    load_dotenv()
    settings = Settings()
    configure_logging(settings.log_level, service_name="audio")
    base = settings.robot_api_base.rstrip("/")
    stop = threading.Event()

    def heartbeat_loop() -> None:
        with httpx.Client() as client:
            while not stop.wait(_HEARTBEAT_S):
                try:
                    _post_listening(client, base, True)
                except httpx.HTTPError as exc:
                    _LOG.warning("Listening heartbeat failed: %s", exc)

    _LOG.info(
        "Command prompt (blank line to exit). POSTing commands to %s/commands; "
        "listening heartbeats to %s/audio/listening every %.0fs.",
        base,
        base,
        _HEARTBEAT_S,
    )

    hb_thread = threading.Thread(target=heartbeat_loop, name="audio-heartbeat", daemon=True)
    try:
        with httpx.Client() as client:
            _post_listening(client, base, True)
            hb_thread.start()

            while True:
                line = input("command> ")
                cmd = parse_command_line(line)
                if cmd is None and line.strip() == "":
                    break
                if cmd is None:
                    continue
                payload = {"command": cmd.command.value, "distance_m": cmd.distance_m}
                try:
                    r = client.post(f"{base}/commands", json=payload, timeout=5.0)
                    r.raise_for_status()
                    body = r.json()
                    echo = body.get("command_receipt_echo") if isinstance(body, dict) else None
                    _LOG.info("server: %s", echo or body)
                except httpx.HTTPError as exc:
                    _LOG.error("HTTP error (%s). Is the API running?", exc)
                time.sleep(0)
    except EOFError:
        pass
    finally:
        stop.set()
        try:
            with httpx.Client() as client:
                _post_listening(client, base, False)
        except httpx.HTTPError as exc:
            _LOG.warning("Failed to clear listening flag: %s", exc)
    _LOG.info("Audio service exiting.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
