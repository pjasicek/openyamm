#!/usr/bin/env python3
"""Point a creature project's review viewer at new GLBs and add new clips to its manifest, keeping the previous
manifest as manifest_<old revision>.json (as the rat sprint pilot did). Clip durations are read from the first GLB.

    viewer_manifest.py <viewer dir> <revision> <title> --model <id>=<file>=<label> [...] \
        --clip <name>=<label>=<provenance> [...] [--default-clip <name>]
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("viewer", type=Path)
    parser.add_argument("revision")
    parser.add_argument("title")
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--clip", action="append", default=[])
    parser.add_argument("--default-clip")
    args = parser.parse_args()
    path = args.viewer / "manifest.json"
    manifest = json.loads(path.read_text())
    old = manifest.get("revision", "old")
    if old != args.revision:
        shutil.copyfile(path, args.viewer / f"manifest_{old}.json")
    models = []
    for item in args.model:
        model_id, file, label = item.split("=", 2)
        digest = hashlib.sha256((args.viewer / file).read_bytes()).hexdigest()
        models.append({"id": model_id, "label": label, "url": f"{file}?v={digest[:12]}", "revision": args.revision,
                       "sha256": digest})
    glb = glb_pose.Model(glb_pose.Glb(args.viewer / models[0]["url"].split("?")[0]))
    for item in args.clip:
        name, label, provenance = item.split("=", 2)
        manifest["clips"][name] = {"label": label, "duration": round(float(glb.clip_times(name)[-1]), 6),
                                   "mode": "loop", "provenance": provenance, "anchors": []}
    for name, clip in manifest["clips"].items():
        length = float(glb.clip_times(name)[-1])
        if abs(length - clip["duration"]) > 1e-5:
            sys.exit(f"{name}: manifest {clip['duration']} s, GLB {length} s")
    manifest.update({"revision": args.revision, "model": args.title, "models": models,
                     "default_model": models[0]["id"], "model_sha256": models[0]["sha256"]})
    if args.default_clip:
        manifest["default_clip"] = args.default_clip
    path.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{path}: revision {args.revision}, {len(models)} models, {len(manifest['clips'])} clips")


if __name__ == "__main__":
    main()
