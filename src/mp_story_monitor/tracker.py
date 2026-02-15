"""Progress tracker: writes _progress.json, optional viewer HTML, optional sound."""

import json
import os
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Sequence

# #region agent log
DEBUG_LOG = Path("/Users/senzhang/mp-llp/.cursor/debug.log")
def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)}) + "\n")
    except Exception:
        pass
# #endregion

HEARTBEAT_INTERVAL_SEC = 30

# Contract: filenames written under story_path (consumers may read these)
PROGRESS_JSON_FILENAME = "_progress.json"
PHASE_STATUS_FILENAME = "_phase_status.txt"
VIEWER_HTML_FILENAME = "progress_viewer.html"
NOTIFICATION_STORY_PROGRESS_FILENAME = "notification-story-progress.mp3"
NOTIFICATION_STORY_FINISH_FILENAME = "notification-story-finish.mp3"
NOTIFICATION_ERROR_FILENAME = "notification-error.mp3"

DEFAULT_PHASE_ORDER: tuple = ("reddit", "director", "production", "assembly")


class ProgressTracker:
    """Tracks pipeline phase progress and copies the story monitor viewer into the story folder.

    Usage:
        tracker = ProgressTracker(story_path, job_id="...", workflow="two_girl_reddit")
        tracker.ensure_viewer()
        tracker.start("reddit")
        # ... run phase ...
        tracker.finish("reddit")
        tracker.start("director")
        # ...
        tracker.complete()
    """

    def __init__(
        self,
        story_path: Path,
        *,
        job_id: str = "",
        workflow: str = "",
        phase_names: Sequence[str] = (),
    ):
        self.story_path = Path(story_path)
        self.job_id = job_id
        self.workflow = workflow or "story"
        self._phase_names: tuple = tuple(phase_names) if phase_names else DEFAULT_PHASE_ORDER
        self._phases: Dict[str, str] = {p: "pending" for p in self._phase_names}
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    def _write_phase_status(self, phase: str) -> None:
        try:
            (self.story_path / PHASE_STATUS_FILENAME).write_text(
                f"phase={phase}\n", encoding="utf-8"
            )
        except Exception:
            pass

    def _write_progress(self, current_step: str = "") -> None:
        try:
            payload = {
                "job_id": self.job_id,
                "workflow": self.workflow,
                "updated_ts": datetime.now(timezone.utc).isoformat(),
                "phases": dict(self._phases),
                "phase_order": list(self._phase_names),
                "current_step": current_step,
                "story_path": str(self.story_path.resolve()),
            }
            # #region agent log
            _agent_log("tracker.py:_write_progress", "Writing _progress.json", {"story_path": str(self.story_path.resolve()), "updated_ts": payload["updated_ts"], "phases": payload["phases"]}, "H1,H3")
            # #endregion
            (self.story_path / PROGRESS_JSON_FILENAME).write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _play_sound(self, phase: str = "") -> None:
        if not os.environ.get("PROGRESS_SOUND"):
            return
        try:
            parent = Path(__file__).resolve().parent
            # Use story-finish sound when director phase completes; otherwise progress sound
            if phase == "director":
                name = NOTIFICATION_STORY_FINISH_FILENAME
            else:
                name = NOTIFICATION_STORY_PROGRESS_FILENAME
            in_story = self.story_path / name
            pkg_path = parent / name
            path = in_story if in_story.exists() else pkg_path
            if path.exists():
                subprocess.run(
                    ["afplay", str(path)],
                    capture_output=True,
                    timeout=5,
                )
        except Exception:
            pass

    def ensure_viewer(self) -> None:
        """Copy progress_viewer.html and notification sound into story folder (idempotent)."""
        try:
            parent = Path(__file__).resolve().parent
            template = parent / VIEWER_HTML_FILENAME
            if template.exists():
                shutil.copy(template, self.story_path / VIEWER_HTML_FILENAME)
            for name in (NOTIFICATION_STORY_PROGRESS_FILENAME, NOTIFICATION_STORY_FINISH_FILENAME, NOTIFICATION_ERROR_FILENAME):
                sound_src = parent / name
                if sound_src.exists():
                    shutil.copy(sound_src, self.story_path / name)
        except Exception:
            pass

    def _heartbeat_loop(self) -> None:
        """Refresh _progress.json every HEARTBEAT_INTERVAL_SEC so 'Last updated' shows process is alive."""
        # #region agent log
        _agent_log("tracker.py:_heartbeat_loop", "Heartbeat loop started", {"story_path": str(self.story_path.resolve())}, "H3")
        # #endregion
        while not self._heartbeat_stop.wait(timeout=HEARTBEAT_INTERVAL_SEC):
            self._write_progress()

    def start(self, phase: str, current_step: str = "") -> None:
        """Mark phase as running and persist. Start heartbeat so 'Last updated' refreshes during long phases."""
        if phase not in self._phases:
            self._phases[phase] = "pending"
        self._phases[phase] = "running"
        self._write_phase_status(phase)
        self._write_progress(current_step=current_step)
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def finish(self, phase: str, play_sound: bool = True, current_step: str = "") -> None:
        """Mark phase as done, optionally play sound, persist. Stop heartbeat."""
        self._heartbeat_stop.set()
        self._phases[phase] = "done"
        self._write_progress(current_step=current_step)
        if play_sound:
            self._play_sound(phase)

    def complete(self) -> None:
        """Mark all phases done and set status to complete. Stop heartbeat."""
        self._heartbeat_stop.set()
        for p in self._phase_names:
            self._phases[p] = "done"
        self._write_phase_status("complete")
        self._write_progress()
