#!/usr/bin/env python3
"""Serves update folders over HTTP with byte ranges, like the nginx release host, as a local channel for the install
check (packaging/publish_release.py check). A request is answered from the first folder that has the file; with
--fallback, a missing file redirects to the same path there (the packs a release reuses from the server).

Usage: serve_channel.py --port PORT [--fallback URL] FOLDER [FOLDER...]"""

import argparse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import re
import sys
import urllib.parse


def make_handler(folders, fallback):
    class ChannelHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            # The channel lives below /updates/, as on the server.
            relative = urllib.parse.unquote(urllib.parse.urlsplit(path).path)
            relative = relative[len("/updates"):] if relative.startswith("/updates/") else relative
            parts = [part for part in relative.split("/") if part not in ("", ".", "..")]
            for folder in folders:
                candidate = os.path.join(folder, *parts)
                if os.path.exists(candidate):
                    return candidate
            return os.path.join(folders[0], *parts)

        def send_head(self):
            path = self.translate_path(self.path)
            if not os.path.exists(path) and fallback:
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", fallback.rstrip("/") + "/" + self.path.split("/updates/", 1)[-1])
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            match = re.fullmatch(r"bytes=(\d+)-", self.headers.get("Range", ""))
            if not match or not os.path.isfile(path):
                return super().send_head()
            size = os.path.getsize(path)
            start = int(match.group(1))
            if start >= size:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return None
            stream = open(path, "rb")
            stream.seek(start)
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{size - 1}/{size}")
            self.send_header("Content-Length", str(size - start))
            self.end_headers()
            return stream

        def log_message(self, format, *args):
            sys.stderr.write("serve_channel: " + format % args + "\n")

    return ChannelHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--fallback", help="Base URL that missing files redirect to")
    parser.add_argument("folders", nargs="+")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.folders, args.fallback))
    server.serve_forever()


if __name__ == "__main__":
    main()
