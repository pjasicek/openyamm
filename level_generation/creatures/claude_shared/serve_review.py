#!/usr/bin/env python3
"""Review web server for the creature viewers: a plain static server on 127.0.0.1 that tells the browser never to cache.

Viewers reinstall GLBs and manifests under the same names; with the default http.server headers a browser may keep showing
an older revision for hours (PeasantF4 r31 shown after r40 was installed, 2026-11-04). Run from the repository root:
    python3 level_generation/creatures/claude_shared/serve_review.py [port]
"""
import functools
import http.server
import sys


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8912
    handler = functools.partial(NoCacheHandler, directory='.')
    with http.server.ThreadingHTTPServer(('127.0.0.1', port), handler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
