"""Command protocol for monitor control actions."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

COMMANDS_FILENAME = "_commands.json"


class CommandAction(str, Enum):
    RESET_ASSET = "reset_asset"
    RESET_SCENE = "reset_scene"
    RESET_CHAPTER = "reset_chapter"
    RESET_STORY = "reset_story"


@dataclass
class Command:
    id: str
    action: CommandAction
    target: str
    status: str = "pending"
    created_at: str = ""
    processed_at: Optional[str] = None
    result: Optional[str] = None


def create_command(action: CommandAction, target: str) -> Command:
    """Create a new command with a unique ID and timestamp."""
    cmd_id = f"cmd_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    return Command(
        id=cmd_id,
        action=action,
        target=target,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def read_commands(story_path: Path) -> List[Command]:
    """Read commands from _commands.json in the given directory.

    Returns an empty list if the file does not exist or is malformed.
    """
    cmd_file = story_path / COMMANDS_FILENAME
    if not cmd_file.exists():
        return []
    try:
        data = json.loads(cmd_file.read_text(encoding="utf-8"))
        return [Command(**c) for c in data.get("commands", [])]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def write_commands(story_path: Path, commands: List[Command]) -> None:
    """Write commands to _commands.json in the given directory."""
    cmd_file = story_path / COMMANDS_FILENAME
    payload = {"commands": [asdict(c) for c in commands]}
    cmd_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def mark_command_done(cmd: Command, result: str = "") -> None:
    """Mark a command as done with an optional result message."""
    cmd.status = "done"
    cmd.result = result
    cmd.processed_at = datetime.now(timezone.utc).isoformat()
