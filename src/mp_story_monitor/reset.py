"""Reset logic: find and delete asset output files with cascade support."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Set

from mp_logger import get_logger

logger = get_logger("story_monitor", tag="RESET")

# Extensions by asset type
_EXT_MAP = {
    "image": {".png", ".jpg", ".jpeg", ".webp"},
    "audio": {".wav", ".mp3", ".flac"},
    "video": {".mp4", ".webm", ".mov"},
    "text": {".txt"},
}
_ALL_EXTS: Set[str] = set()
for _exts in _EXT_MAP.values():
    _ALL_EXTS |= _exts


def _slug(name: str) -> str:
    """Normalize asset name to match production's slug logic."""
    return name.lower().replace("_", "-").replace(" ", "-")


def find_asset_output_files(
    story_path: Path,
    asset_name: str,
    asset_types: Optional[List[str]] = None,
) -> List[Path]:
    """Find all output files matching an asset name slug anywhere under story_path."""
    slug = _slug(asset_name)
    exts: Set[str] = set()
    if asset_types:
        for t in asset_types:
            exts |= _EXT_MAP.get(t, set())
    if not exts:
        exts = _ALL_EXTS

    found = []
    for f in story_path.rglob("*"):
        if not f.is_file() or f.stat().st_size == 0:
            continue
        if f.suffix.lower() not in exts:
            continue
        if slug in _slug(f.stem):
            found.append(f)
    return found


def delete_asset_outputs(
    story_path: Path,
    asset_name: str,
    scene_hint: Optional[str] = None,
) -> int:
    """Delete output files for an asset. Returns count of files deleted."""
    slug = _slug(asset_name)
    deleted = 0

    # Search in scene_hint dir first, then all
    search_paths: List[Path] = []
    if scene_hint:
        for d in story_path.rglob(f"*{scene_hint}*"):
            if d.is_dir():
                search_paths.append(d)
    search_paths.append(story_path)

    seen: Set[Path] = set()
    for base in search_paths:
        for f in base.rglob("*"):
            if f in seen or not f.is_file():
                continue
            seen.add(f)
            if f.suffix.lower() in _ALL_EXTS and slug in _slug(f.stem):
                logger.info(f"Deleting: {f}")
                f.unlink()
                deleted += 1
            # Also delete muxed variants
            elif "_muxed" in f.name and slug in _slug(f.stem):
                logger.info(f"Deleting muxed: {f}")
                f.unlink()
                deleted += 1

    # Delete final_stitched files (downstream of any video reset)
    for stitched in story_path.glob("final_stitched_*.mp4"):
        if stitched not in seen:
            logger.info(f"Deleting stitched: {stitched}")
            stitched.unlink()
            deleted += 1

    return deleted


def reset_scene(story_path: Path, scene_id: str) -> int:
    """Delete all generated output files in a scene directory. scene_id like 'C01_S00'."""
    deleted = 0
    # Extract numeric parts: C01_S00 -> chapter_num="1", scene_num="0"
    match = re.match(r"C(\d+)_S(\d+)", scene_id, re.IGNORECASE)
    if not match:
        logger.warning(f"Invalid scene_id format: {scene_id}")
        return 0
    chapter_num = str(int(match.group(1)))
    scene_num = match.group(2).lstrip("0") or "0"

    for chapter_dir in story_path.iterdir():
        if not chapter_dir.is_dir() or not chapter_dir.name.startswith("Chapter"):
            continue
        ch_match = re.match(r"Chapter(\d+)", chapter_dir.name)
        if not ch_match or str(int(ch_match.group(1))) != chapter_num:
            continue
        for scene_dir in chapter_dir.iterdir():
            if not scene_dir.is_dir():
                continue
            dir_match = re.match(r"scene_(\d+)", scene_dir.name)
            if not dir_match:
                continue
            dir_num = dir_match.group(1).lstrip("0") or "0"
            if dir_num != scene_num:
                continue
            for f in scene_dir.iterdir():
                if f.is_file() and f.suffix.lower() in _ALL_EXTS and f.stat().st_size > 0:
                    logger.info(f"Reset scene: deleting {f}")
                    f.unlink()
                    deleted += 1
    # Also delete final stitched
    for stitched in story_path.glob("final_stitched_*.mp4"):
        logger.info(f"Reset scene: deleting stitched {stitched}")
        stitched.unlink()
        deleted += 1
    return deleted


def reset_chapter(story_path: Path, chapter_id: str) -> int:
    """Delete all generated output files in a chapter (all scenes). chapter_id like 'C01'."""
    deleted = 0
    match = re.match(r"C(\d+)", chapter_id, re.IGNORECASE)
    if not match:
        logger.warning(f"Invalid chapter_id format: {chapter_id}")
        return 0
    chapter_num = str(int(match.group(1)))

    for chapter_dir in story_path.iterdir():
        if not chapter_dir.is_dir() or not chapter_dir.name.startswith("Chapter"):
            continue
        dir_match = re.match(r"Chapter(\d+)", chapter_dir.name)
        if not dir_match:
            continue
        dir_num = str(int(dir_match.group(1)))
        if dir_num != chapter_num:
            continue
        for f in chapter_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in _ALL_EXTS and f.stat().st_size > 0:
                logger.info(f"Reset chapter: deleting {f}")
                f.unlink()
                deleted += 1
    # Also delete final stitched
    for stitched in story_path.glob("final_stitched_*.mp4"):
        logger.info(f"Reset chapter: deleting stitched {stitched}")
        stitched.unlink()
        deleted += 1
    return deleted


def reset_story(story_path: Path) -> int:
    """Delete story.json and all generated outputs to force full regeneration."""
    deleted = 0
    story_json = story_path / "story.json"
    if story_json.exists():
        story_json.unlink()
        logger.info("Reset story: deleted story.json")
        deleted += 1
    for f in story_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in _ALL_EXTS:
            f.unlink()
            deleted += 1
    for pattern in ["final_stitched_*.mp4", "remotion_input.json"]:
        for f in story_path.glob(pattern):
            if f.exists():
                f.unlink()
                deleted += 1
    logger.info(f"Reset story: deleted {deleted} files total")
    return deleted
