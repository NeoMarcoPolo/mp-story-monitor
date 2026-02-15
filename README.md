# mp-story-monitor

Progress tracking and story skeleton viewer for story pipelines. Extracted from mp-auto-generate so any pipeline can depend on it.

## Usage

```python
from mp_story_monitor import ProgressTracker

tracker = ProgressTracker(story_path, job_id="...", workflow="two_girl_reddit")
tracker.ensure_viewer()   # copy progress_viewer.html into story folder
tracker.start("reddit")
# ... run phase ...
tracker.finish("reddit")  # optional: play sound if PROGRESS_SOUND=1
tracker.start("director")
# ...
tracker.complete()
```

## Contract

- **Interface:** `ProgressTracker(story_path, job_id="", workflow="", phase_names=())` with `ensure_viewer()`, `start(phase)`, `finish(phase, play_sound=True)`, `complete()`.
- **Output files under `story_path`:** `_progress.json`, `_phase_status.txt`, `progress_viewer.html` (if viewer ensured).
- **Env:** `PROGRESS_SOUND=1` to play sound on `finish()` (macOS `afplay`).
- **Default phases:** `reddit`, `director`, `production`, `assembly`. Override with `phase_names=` for other workflows.

Pipelines (e.g. mp-auto-generate) write **`_progress.json`** via the tracker and may write **`_director_progress.json`** separately for the story skeleton. The viewer HTML polls both and shows phases plus skeleton (title, logline, asset counts, chapters/scenes).

## QA/QC: Inspect skeleton before production

The progress viewer shows the full story skeleton (title, logline, Images/Audio/Video/Text counts, chapters, and every scene with narrative and asset counts) when the Director phase has data. The skeleton stays visible when Director is **running** and **done**, so you can inspect it before Production. When Director is done and Production is pending, a banner appears: *"Skeleton complete. Inspect all items below before production runs."*

## Serving the viewer

Run an HTTP server from the **story folder** (the folder that contains `_progress.json` and `progress_viewer.html`):

- `python -m http.server 8765`
- Or use your pipeline’s progress server script (e.g. `serve_progress.py` from mp-auto-generate). **Built-in server in this package:** `python -m mp_story_monitor.serve_progress --port 8081 /path/to/story` (no-cache for JSON). Pipelines call `mp_story_monitor.serve_progress.serve(story_path, port)`.

## Exports

- `ProgressTracker`, `PROGRESS_JSON_FILENAME`, `PHASE_STATUS_FILENAME`, `VIEWER_HTML_FILENAME`, `DEFAULT_PHASE_ORDER`
