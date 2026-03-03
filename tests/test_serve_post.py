# mp-story-monitor/tests/test_serve_post.py
import json
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


def _start_server(story_path: Path, port: int):
    from mp_story_monitor.serve_progress import serve
    t = threading.Thread(target=serve, args=(story_path, port), daemon=True)
    t.start()
    time.sleep(0.5)
    return t


def _post(port: int, endpoint: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{endpoint}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def test_post_reset_asset():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "_progress.json").write_text("{}")
        # Create a fake asset file
        (p / "test_asset.png").write_bytes(b"fake")
        _start_server(p, 18091)
        resp = _post(18091, "/api/reset-asset", {"asset_name": "test_asset"})
        assert resp["ok"] is True
        assert "command_id" in resp


def test_post_reset_scene():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "_progress.json").write_text("{}")
        scene = p / "Chapter01_test" / "scene_00"
        scene.mkdir(parents=True)
        (scene / "test.png").write_bytes(b"fake")
        _start_server(p, 18092)
        resp = _post(18092, "/api/reset-scene", {"scene_id": "C01_S00"})
        assert resp["ok"] is True


def test_get_commands():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "_progress.json").write_text("{}")
        _start_server(p, 18093)
        # First reset something to create a command
        _post(18093, "/api/reset-asset", {"asset_name": "x"})
        req = urllib.request.Request(f"http://127.0.0.1:18093/api/commands")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        assert "commands" in data
        assert len(data["commands"]) >= 1
