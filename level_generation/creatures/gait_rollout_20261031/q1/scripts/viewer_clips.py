#!/usr/bin/env python3
"""Give review-viewer GLBs (tier bakes made by a project's viewer_tiers.py, possibly older than the installed model's
floor fixes) every clip of the candidate export, so the viewer plays exactly what will be installed: runs
../../claude_shared/graft_clips.py --replace with every clip of the export, in place.

    viewer_clips.py <export.glb> <viewer.glb> [<viewer.glb> ...]
"""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402

GRAFT = Path(__file__).resolve().parents[3] / "claude_shared" / "graft_clips.py"


def main():
    export = Path(sys.argv[1])
    clips = [a["name"] for a in glb_pose.Glb(export).json.get("animations", [])]
    for viewer in map(Path, sys.argv[2:]):
        temporary = viewer.with_suffix(".tmp.glb")
        arguments = [sys.executable, str(GRAFT), str(viewer), str(export), str(temporary), "--replace"]
        for clip in clips:
            arguments += ["--clip", clip]
        subprocess.run(arguments, check=True, stdout=subprocess.DEVNULL)
        temporary.replace(viewer)
        print(f"{viewer}: {len(clips)} clips from {export.name}")


if __name__ == "__main__":
    main()
