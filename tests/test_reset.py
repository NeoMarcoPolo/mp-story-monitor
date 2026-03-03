# mp-story-monitor/tests/test_reset.py
import tempfile
from pathlib import Path
from mp_story_monitor.reset import (
    find_asset_output_files,
    delete_asset_outputs,
    reset_scene,
    reset_chapter,
)


def _make_story_dir(tmp: str) -> Path:
    """Create a minimal story directory with fake outputs."""
    p = Path(tmp)
    # Story-level
    (p / "story_00_chara1_chara1-concept-sheet.png").touch()
    # Chapter + scene
    scene = p / "Chapter01_idle_hum" / "scene_00"
    scene.mkdir(parents=True)
    (scene / "scene_C01_S00_keyframe_scene-c01-s00-keyframe-keyframe.png").write_bytes(b"fake")
    (scene / "scene_00_nextscene.mp4").write_bytes(b"fake")
    (scene / "scene_00_wan.mp4").write_bytes(b"fake")
    (scene / "scene_00_ltx.mp4").write_bytes(b"fake")
    (scene / "scene_00_infinitetalk.mp4").write_bytes(b"fake")
    (scene / "scene_00_nextscene_muxed.mp4").write_bytes(b"fake")
    # Scene 01
    scene1 = p / "Chapter01_idle_hum" / "scene_01"
    scene1.mkdir(parents=True)
    (scene1 / "scene_C01_S01_keyframe_scene-c01-s01-keyframe-keyframe.png").write_bytes(b"fake")
    (scene1 / "scene_01_nextscene.mp4").write_bytes(b"fake")
    # Final stitched
    (p / "final_stitched_nextscene.mp4").write_bytes(b"fake")
    return p


def test_find_asset_output_files():
    with tempfile.TemporaryDirectory() as tmp:
        p = _make_story_dir(tmp)
        files = find_asset_output_files(p, "scene-c01-s00-keyframe-keyframe", ["image"])
        assert len(files) >= 1
        assert any("keyframe" in f.name for f in files)


def test_delete_asset_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        p = _make_story_dir(tmp)
        scene = p / "Chapter01_idle_hum" / "scene_00"
        assert (scene / "scene_00_nextscene.mp4").exists()
        deleted = delete_asset_outputs(p, "nextscene", scene_hint="scene_00")
        assert deleted >= 1


def test_reset_scene_deletes_all_scene_files():
    with tempfile.TemporaryDirectory() as tmp:
        p = _make_story_dir(tmp)
        scene = p / "Chapter01_idle_hum" / "scene_00"
        before = len(list(scene.iterdir()))
        assert before > 0
        count = reset_scene(p, "C01_S00")
        after = len([f for f in scene.iterdir() if f.stat().st_size > 0])
        assert after == 0 or count > 0


def test_reset_chapter_deletes_chapter_and_scenes():
    with tempfile.TemporaryDirectory() as tmp:
        p = _make_story_dir(tmp)
        count = reset_chapter(p, "C01")
        scene00 = p / "Chapter01_idle_hum" / "scene_00"
        scene01 = p / "Chapter01_idle_hum" / "scene_01"
        files_00 = [f for f in scene00.iterdir() if f.stat().st_size > 0] if scene00.exists() else []
        files_01 = [f for f in scene01.iterdir() if f.stat().st_size > 0] if scene01.exists() else []
        assert len(files_00) == 0
        assert len(files_01) == 0
        assert count > 0
