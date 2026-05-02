"""Optional policy helpers layered above the state machine (extension point)."""

from __future__ import annotations

from contracts.commands import HighLevelCommand, HighLevelCommandType


class BehaviorPolicy:
    """
    Maps external events to canonical commands.

    Reserved for richer rules (e.g. geofencing) without bloating the state machine.
    """

    def normalize(self, cmd: HighLevelCommand) -> HighLevelCommand:
        """Normalize synonyms or legacy labels."""

        if cmd.command == HighLevelCommandType.STOP:
            return HighLevelCommand(command=HighLevelCommandType.EMERGENCY_STOP)
        return cmd
