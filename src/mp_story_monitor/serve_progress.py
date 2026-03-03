"""
Serve the progress viewer and story JSON from a story folder.

Use this so the browser can open progress_viewer.html and poll _progress.json /
_director_progress.json with no-cache. Caller is responsible for resolving the
story path (e.g. from config + job in mp-auto-generate).

Usage:
  python -m mp_story_monitor.serve_progress --port 8081 /path/to/story
  # or from code:
  from mp_story_monitor.serve_progress import serve
  serve(Path("/path/to/story"), port=8081)
"""
import json
import logging
import os
import socketserver
from pathlib import Path

from mp_story_monitor.tracker import ProgressTracker, VIEWER_HTML_FILENAME

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8081


def _ensure_story_folder(story_path: Path) -> None:
    """Create folder if needed and ensure viewer + minimal _progress.json exist."""
    story_path = Path(story_path).resolve()
    if not story_path.exists():
        story_path.mkdir(parents=True, exist_ok=True)
        try:
            ProgressTracker(story_path, job_id="", workflow="").ensure_viewer()
            (story_path / "_progress.json").write_text(
                '{"phases":{},"phase_order":["reddit","director","production","assembly"],"updated_ts":""}',
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to ensure story folder setup: {e}")


def serve(story_path: Path, port: int = DEFAULT_PORT) -> None:
    """Run HTTP server for the given story folder until interrupted."""
    import http.server

    story_path = Path(story_path).resolve()
    _ensure_story_folder(story_path)
    if not (story_path / "_progress.json").exists():
        print("No _progress.json yet. Start the pipeline; the viewer will update when it runs.")

    print(f"Serving: {story_path}")
    print(f"Open: http://localhost:{port}/progress_viewer.html")
    print("Press Ctrl+C to stop.")

    package_dir = Path(__file__).resolve().parent
    viewer_file = package_dir / "progress_viewer.html"
    viewer_path_for_handler = viewer_file if viewer_file.exists() else None
    if viewer_path_for_handler:
        print(f"Viewer served from package: {viewer_path_for_handler}")

    os.chdir(story_path)

    class _ProgressHandler(http.server.SimpleHTTPRequestHandler):
        viewer_path = viewer_path_for_handler
        _story_path = story_path

        def _send_no_cache_headers(self) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")

        def do_GET(self) -> None:
            path_clean = (self.path or "").split("?")[0].strip("/")
            if self.viewer_path and (
                path_clean == VIEWER_HTML_FILENAME
                or (self.path or "").rstrip("/").endswith(VIEWER_HTML_FILENAME)
            ):
                try:
                    content = self.viewer_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self._send_no_cache_headers()
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logger.warning(f"Failed to serve viewer HTML: {e}")
            if path_clean == "_progress.json":
                try:
                    p = self._story_path / "_progress.json"
                    if p.exists():
                        content = p.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.send_header("Content-Length", str(len(content)))
                        self._send_no_cache_headers()
                        self.end_headers()
                        self.wfile.write(content)
                        return
                except Exception as e:
                    logger.warning(f"Failed to serve _progress.json: {e}")
            if path_clean == "_director_progress.json":
                try:
                    p = self._story_path / "_director_progress.json"
                    if p.exists():
                        content = p.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.send_header("Content-Length", str(len(content)))
                        self._send_no_cache_headers()
                        self.end_headers()
                        self.wfile.write(content)
                        return
                except Exception as e:
                    logger.warning(f"Failed to serve _director_progress.json: {e}")
            if path_clean == "api/commands":
                from mp_story_monitor.commands import read_commands
                from dataclasses import asdict
                cmds = read_commands(self._story_path)
                payload = {"commands": [asdict(c) for c in cmds]}
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def do_POST(self) -> None:
            """Handle POST requests for control actions."""
            from mp_story_monitor.commands import (
                CommandAction, create_command, read_commands, write_commands,
            )
            from mp_story_monitor.reset import (
                delete_asset_outputs, reset_scene, reset_chapter, reset_story,
            )

            path_clean = (self.path or "").split("?")[0].strip("/")
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}

            result = {"ok": False, "error": "Unknown endpoint"}

            if path_clean == "api/reset-asset":
                asset_name = body.get("asset_name", "")
                if not asset_name:
                    result = {"ok": False, "error": "Missing asset_name"}
                else:
                    cmd = create_command(CommandAction.RESET_ASSET, asset_name)
                    deleted = delete_asset_outputs(self._story_path, asset_name)
                    cmds = read_commands(self._story_path)
                    cmds.append(cmd)
                    write_commands(self._story_path, cmds)
                    result = {"ok": True, "command_id": cmd.id, "files_deleted": deleted}

            elif path_clean == "api/reset-scene":
                scene_id = body.get("scene_id", "")
                if not scene_id:
                    result = {"ok": False, "error": "Missing scene_id"}
                else:
                    cmd = create_command(CommandAction.RESET_SCENE, scene_id)
                    deleted = reset_scene(self._story_path, scene_id)
                    cmds = read_commands(self._story_path)
                    cmds.append(cmd)
                    write_commands(self._story_path, cmds)
                    result = {"ok": True, "command_id": cmd.id, "files_deleted": deleted}

            elif path_clean == "api/reset-chapter":
                chapter_id = body.get("chapter_id", "")
                if not chapter_id:
                    result = {"ok": False, "error": "Missing chapter_id"}
                else:
                    cmd = create_command(CommandAction.RESET_CHAPTER, chapter_id)
                    deleted = reset_chapter(self._story_path, chapter_id)
                    cmds = read_commands(self._story_path)
                    cmds.append(cmd)
                    write_commands(self._story_path, cmds)
                    result = {"ok": True, "command_id": cmd.id, "files_deleted": deleted}

            elif path_clean == "api/reset-story":
                cmd = create_command(CommandAction.RESET_STORY, "*")
                deleted = reset_story(self._story_path)
                cmds = read_commands(self._story_path)
                cmds.append(cmd)
                write_commands(self._story_path, cmds)
                result = {"ok": True, "command_id": cmd.id, "files_deleted": deleted}

            response_body = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response_body)

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), _ProgressHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Port {port} in use. Try: python -m mp_story_monitor.serve_progress --port {port + 1} <story_path>")
        raise


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Serve progress viewer from a story folder (e.g. where _progress.json is written)."
    )
    parser.add_argument(
        "story_path",
        type=Path,
        help="Path to the story folder (created if missing)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind (default {DEFAULT_PORT})",
    )
    args = parser.parse_args()
    serve(args.story_path, port=args.port)


if __name__ == "__main__":
    main()
