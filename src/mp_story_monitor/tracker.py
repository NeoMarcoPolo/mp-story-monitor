"""Progress tracker: writes _progress.json, optional viewer HTML, optional sound."""

import json
import os
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Sequence

HEARTBEAT_INTERVAL_SEC = 30

# Contract: filenames written under story_path (consumers may read these)
PROGRESS_JSON_FILENAME = "_progress.json"
PHASE_STATUS_FILENAME = "_phase_status.txt"
VIEWER_HTML_FILENAME = "progress_viewer.html"

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
            }
            (self.story_path / PROGRESS_JSON_FILENAME).write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _play_sound(self) -> None:
        if not os.environ.get("PROGRESS_SOUND"):
            return
        try:
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                capture_output=True,
                timeout=2,
            )
        except Exception:
            pass

    def ensure_viewer(self) -> None:
        """Copy progress_viewer.html into story folder (idempotent)."""
        try:
            template = Path(__file__).resolve().parent / VIEWER_HTML_FILENAME
            if template.exists():
                shutil.copy(template, self.story_path / VIEWER_HTML_FILENAME)
        except Exception:
            pass

    def _heartbeat_loop(self) -> None:
        """Refresh _progress.json every HEARTBEAT_INTERVAL_SEC so 'Last updated' shows process is alive."""
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
            self._play_sound()

    def complete(self) -> None:
        """Mark all phases done and set status to complete. Stop heartbeat."""
        self._heartbeat_stop.set()
        for p in self._phase_names:
            self._phases[p] = "done"
        self._write_phase_status("complete")
        self._write_progress()
