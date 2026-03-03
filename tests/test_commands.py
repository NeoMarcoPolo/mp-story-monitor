import tempfile
from pathlib import Path
from mp_story_monitor.commands import (
    CommandAction,
    Command,
    create_command,
    read_commands,
    write_commands,
    mark_command_done,
)


def test_create_command_generates_unique_id():
    cmd = create_command(CommandAction.RESET_ASSET, "scene_C01_S00_keyframe")
    assert cmd.id.startswith("cmd_")
    assert cmd.action == CommandAction.RESET_ASSET
    assert cmd.target == "scene_C01_S00_keyframe"
    assert cmd.status == "pending"


def test_write_and_read_commands_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        cmd = create_command(CommandAction.RESET_ASSET, "test_asset")
        write_commands(path, [cmd])
        loaded = read_commands(path)
        assert len(loaded) == 1
        assert loaded[0].id == cmd.id
        assert loaded[0].action == CommandAction.RESET_ASSET


def test_read_commands_returns_empty_when_no_file():
    with tempfile.TemporaryDirectory() as tmp:
        loaded = read_commands(Path(tmp))
        assert loaded == []


def test_mark_command_done():
    cmd = create_command(CommandAction.RESET_SCENE, "C01_S00")
    mark_command_done(cmd, result="Reset 5 assets")
    assert cmd.status == "done"
    assert cmd.result == "Reset 5 assets"
    assert cmd.processed_at is not None


def test_append_command_preserves_existing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        cmd1 = create_command(CommandAction.RESET_ASSET, "asset_a")
        write_commands(path, [cmd1])
        cmd2 = create_command(CommandAction.RESET_ASSET, "asset_b")
        existing = read_commands(path)
        existing.append(cmd2)
        write_commands(path, existing)
        loaded = read_commands(path)
        assert len(loaded) == 2
