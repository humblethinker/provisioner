#!/usr/bin/env python3
"""Scout dashboard API. Browser automation runs in the separate worker container."""
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
JOBS = DATA / "jobs.json"
SCAN_REQUEST = DATA / "scan.request"
APPLICATION_REQUESTS = DATA / "application_requests.json"


def load_jobs() -> list[dict]:
    if not JOBS.exists():
        return []
    return json.loads(JOBS.read_text())


class Handler(SimpleHTTPRequestHandler):
    def json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/jobs":
            return self.json_response(200, {"jobs": load_jobs()})
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/scans":
            DATA.mkdir(exist_ok=True)
            SCAN_REQUEST.write_text("requested")
            return self.json_response(202, {"status": "queued"})
        if self.path != "/api/applications":
            return self.json_response(404, {"error": "Not found"})
        DATA.mkdir(exist_ok=True)
        size = int(self.headers.get("Content-Length", "0"))
        try:
            request = json.loads(self.rfile.read(size))
            job_id = request["job_id"]
        except (json.JSONDecodeError, KeyError):
            return self.json_response(400, {"error": "job_id is required"})
        queued = json.loads(APPLICATION_REQUESTS.read_text()) if APPLICATION_REQUESTS.exists() else []
        queued.append({"job_id": job_id})
        APPLICATION_REQUESTS.write_text(json.dumps(queued))
        return self.json_response(202, {"status": "queued", "artifact_url": f"/data/artifacts/{job_id}.pdf"})


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(os.getenv("PORT", "8000"))
    print(f"Scout dashboard listening on http://127.0.0.1:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
