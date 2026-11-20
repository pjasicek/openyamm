#!/usr/bin/env python3
"""Run the local OpenYAMM / MM9 FX viewer (requires PyYAML)."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import struct
from urllib.parse import parse_qs, urlsplit
import webbrowser

from assets import Assets

HERE = Path(__file__).resolve().parent
DEFAULT_REFERENCE = HERE.parents[2] / "mm9"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path(os.environ.get("MM9_REFERENCE", DEFAULT_REFERENCE)))
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check-assets", action="store_true", help="Decode all referenced assets and exit")
    args = parser.parse_args()
    if not (args.reference / "extracted/CLIENTFX/CLIENTFX/SPELLS.fxf").is_file():
        parser.error("Cannot find SPELLS.fxf; set --reference to the OpenMM9/reference directory")
    assets = Assets(args.reference)
    if args.check_assets:
        refs = {frame for sprite in assets.sprites.values() for frame in sprite["frames"]}
        models = set()
        for group in assets.groups:
            for key in group["keys"]:
                for prop in key["properties"]:
                    if prop["type"] == 7 and not prop["value"].endswith("|..."):
                        ref = prop["value"].split("|", 1)[1].replace("\\", "/").lower()
                        if ref.endswith(".dtx") and ref in assets.index:
                            refs.add(ref)
                        if ref.endswith(".abc") and ref in assets.index:
                            models.add(ref)
        for ref in sorted(refs):
            assets.texture(ref)
        for ref in sorted(models):
            model = assets.model(ref)
            print(ref, len(model["pieces"]), "pieces,", len(model["nodes"]), "nodes,",
                  model["animation"]["name"] if model["animation"] else "no animation")
        print(f"Decoded {len(refs)} textures, {len(assets.sprites)} sprites, {len(models)} models.")
        for effect, problems in assets.problems.items():
            for problem in problems:
                print(effect + ": " + problem)
        return

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlsplit(self.path)
            ref = parse_qs(request.query).get("name", [""])[0]
            try:
                if request.path == "/api/catalog":
                    data, mime = json.dumps(assets.catalog()).encode(), "application/json"
                elif request.path == "/api/texture":
                    data, mime = assets.texture(ref), "image/png"
                elif request.path == "/api/model":
                    data, mime = json.dumps(assets.model(ref), separators=(",", ":")).encode(), "application/json"
                elif request.path == "/api/sound" and ref.endswith(".wav"):
                    data, mime = assets.index[ref].read_bytes(), "audio/wav"
                else:
                    static = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css",
                              "/app.mjs": "app.mjs", "/simulation.mjs": "simulation.mjs",
                              "/render.mjs": "render.mjs", "/math.mjs": "math.mjs"}
                    name = static[request.path]
                    data = (HERE / name).read_bytes()
                    mime = ("text/html" if name.endswith("html") else "text/css" if name.endswith("css")
                            else "text/javascript")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(data)
            except (KeyError, FileNotFoundError):
                self.send_error(404, "Asset not found")
            except (ValueError, struct.error) as error:
                self.send_error(422, str(error))
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format, *args):
            if args and str(args[1] if len(args) > 1 else "") not in ("200", "304"):
                super().log_message(format, *args)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"OpenYAMM FX viewer: {url}\n{len(assets.groups)} effects. Ctrl+C stops the viewer.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
