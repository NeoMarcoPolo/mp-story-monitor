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
            super().do_GET()

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
