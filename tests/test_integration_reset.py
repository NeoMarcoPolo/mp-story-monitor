# mp-story-monitor/tests/test_integration_reset.py
"""End-to-end: create fake story dir, start server, POST reset, verify files deleted and commands written."""
import json
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


def test_full_reset_flow():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        # Setup: fake story structure
        (p / "_progress.json").write_text(json.dumps({"phases": {"production": "running"}}))
        scene = p / "Chapter01_test" / "scene_00"
        scene.mkdir(parents=True)
        keyframe = scene / "scene-c01-s00-keyframe.png"
        keyframe.write_bytes(b"fakeimg")
        video = scene / "scene_00_nextscene.mp4"
        video.write_bytes(b"fakevid")
        stitched = p / "final_stitched_nextscene.mp4"
        stitched.write_bytes(b"fakestitched")

        # Start server
        from mp_story_monitor.serve_progress import serve
        t = threading.Thread(target=serve, args=(p, 18099), daemon=True)
        t.start()
        time.sleep(0.5)

        # Reset scene
        body = json.dumps({"scene_id": "C01_S00"}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:18099/api/reset-scene",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())

        assert result["ok"] is True
        assert result["files_deleted"] >= 2

        # Verify files deleted
        assert not keyframe.exists() or keyframe.stat().st_size == 0
        assert not video.exists() or video.stat().st_size == 0
        assert not stitched.exists()

        # Verify command written
        cmd_file = p / "_commands.json"
        assert cmd_file.exists()
        cmds = json.loads(cmd_file.read_text())
        assert len(cmds["commands"]) == 1
        assert cmds["commands"][0]["action"] == "reset_scene"
