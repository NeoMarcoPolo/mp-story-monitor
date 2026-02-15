import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Ensure we are in the right directory or use absolute paths
base_dir = Path("/Users/senzhang/mp-llp/mp-story-monitor")
test_dir = base_dir / "ui_test"
src_html = base_dir / "src/mp_story_monitor/progress_viewer.html"

test_dir.mkdir(exist_ok=True)

progress_data = {
    "job_id": "job-alpha-99",
    "workflow": "two_girl_reddit_story",
    "updated_ts": datetime.now(timezone.utc).isoformat(),
    "phases": {
        "reddit": "done",
        "director": "running",
        "production": "pending",
        "assembly": "pending"
    },
    "phase_order": ["reddit", "director", "production", "assembly"],
    "current_step": "Generating aesthetic description for Chapter 2...",
    "story_path": str(test_dir.resolve())
}

director_data = {
    "title": "The Quantum Barista",
    "logline": "A physicist accidentally invents a coffee machine that pours drinks from parallel universes.",
    "max_chapter_workers": 4,
    "assets_by_type": {
        "image": 12,
        "audio": 8,
        "video": 0,
        "text": 45
    },
    "chapters": [
        {
            "title": "Chapter 1: The Grind",
            "scene_count": 3,
            "scenes": [
                {
                    "name": "Scene 1: Morning Routine",
                    "summary": "Dr. Aris wakes up and realizes he is late.",
                    "assets_count": 5,
                    "assets_by_type": {"image": 2, "text": 3},
                    "assets": [
                        {"type": "image", "workflow": "flux_dev", "status": "done", "params": {
                            "prompt": "Close up of an alarm clock showing 8:00 AM, dusty room, morning light, volumetric fog",
                            "negative_prompt": "blurry, distorted, watermarks",
                            "seed": 12345,
                            "aspect_ratio": "16:9"
                        }},
                        {"type": "image", "workflow": "flux_dev", "status": "pending", "params": {
                            "prompt": "Dr. Aris jumping out of bed, panicked expression, messy hair, pajamas",
                            "style_preset": "cinematic"
                        }},
                        {"type": "text", "workflow": "comfy_sound", "status": "done", "params": {
                            "prompt": "Sound effect: Alarm ringing loudly",
                            "duration": 5.0
                        }},
                        {"type": "text", "workflow": "elevenlabs_tts", "status": "done", "params": {
                            "text": "I never thought today would be the end.",
                            "voice_id": "TaxTax",
                            "stability": 0.5
                        }},
                         {"type": "text", "workflow": "gpt-4", "status": "done", "params": {"prompt": "Dialogue: Aris: 'Not again!'"}}
                    ]
                },
                {
                    "name": "Scene 2: Lab Accident",
                    "summary": "Spilling dark matter into the espresso.",
                    "assets_count": 7,
                    "assets_by_type": {"image": 3, "audio": 2, "text": 2}
                },
                {
                    "name": "Scene 3: The First Sip",
                    "summary": "Tasting the void.",
                    "assets_count": 0,
                    "assets_by_type": {}
                }
            ]
        },
        {
            "title": "Chapter 2: Caffeine Jitters",
            "scene_count": 0,
            "scenes": []
        },
         {
            "title": "Chapter 3: The Roast",
            "scene_count": 0,
            "scenes": []
        }
    ]
}

(test_dir / "_progress.json").write_text(json.dumps(progress_data, indent=2))
(test_dir / "_director_progress.json").write_text(json.dumps(director_data, indent=2))

if src_html.exists():
    shutil.copy(src_html, test_dir / "progress_viewer.html")
    print(f"Copied {src_html} to {test_dir}")
else:
    print(f"Source file {src_html} not found!")

print("Test data created in ui_test/")
