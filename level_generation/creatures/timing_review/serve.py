#!/usr/bin/env python3
"""Serve the attack/cast timing review viewer and save its decisions.

    level_generation/creatures/timing_review/serve.py [--port 8765]

Then open http://127.0.0.1:8765/level_generation/creatures/timing_review/
The repository root is served read-only (the viewer loads runtime GLBs, sounds and the vendored three.js from it);
the only write is PUT /api/decisions, which replaces decisions.json next to this script. A PUT must name the version
it replaces (If-Match, from the ETag of the page's GET): a page holding an outdated copy (the file was changed by
apply_decisions.py or by hand) is refused with 409 instead of overwriting the newer file.
"""
import argparse
import hashlib
import json
import os
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DECISIONS = Path(__file__).resolve().parent / "decisions.json"


def decisionsVersion():
    return hashlib.sha1(DECISIONS.read_bytes() if DECISIONS.exists() else b"{}").hexdigest()


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/decisions":
            body = DECISIONS.read_bytes() if DECISIONS.exists() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("ETag", hashlib.sha1(body).hexdigest())
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_PUT(self):
        if self.path != "/api/decisions":
            self.send_error(404)
            return
        if self.headers.get("If-Match") != decisionsVersion():
            self.send_error(409, "decisions.json changed since this page loaded it; reload the page")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            decisions = json.loads(self.rfile.read(length))
            if not isinstance(decisions, dict):
                raise ValueError("decisions must be an object")
        except ValueError as error:
            self.send_error(400, str(error))
            return
        with tempfile.NamedTemporaryFile("w", dir=DECISIONS.parent, prefix="decisions.", suffix=".tmp",
                                         delete=False) as handle:
            json.dump(decisions, handle, indent=1, sort_keys=True)
            handle.write("\n")
            temporary = handle.name
        os.chmod(temporary, 0o644)
        os.replace(temporary, DECISIONS)
        self.send_response(204)
        self.send_header("ETag", decisionsVersion())
        self.end_headers()

    def log_message(self, format, *args):
        if not self.path.startswith("/api/") and " 200 " not in format % args:
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(ROOT)))
    print(f"http://127.0.0.1:{args.port}/level_generation/creatures/timing_review/")
    server.serve_forever()


if __name__ == "__main__":
    main()
