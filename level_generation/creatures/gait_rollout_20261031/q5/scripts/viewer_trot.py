#!/usr/bin/env python3
"""Give the wolf's review viewer (../../mm9_wolf_claude/review/viewer/) the Trot: every clip of the candidate export
grafted into the tier GLBs (../q3/scripts/viewer_clips.py, as q2 and q3 did), the Trot added to the manifest and the
model hashes and revision updated. The previous manifest and GLBs are kept in work/viewer_backup/.

    viewer_trot.py <export.glb> <revision>
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
VIEWER = HERE.parents[1] / "mm9_wolf_claude" / "review" / "viewer"
export, revision = Path(sys.argv[1]).resolve(), sys.argv[2]
glbs = [VIEWER / f"wolf_{t}.glb" for t in "abc"]
subprocess.run([sys.executable, str(HERE.parent / "q3" / "scripts" / "viewer_clips.py"), str(export), *map(str, glbs)],
               check=True)
manifest = json.loads((VIEWER / "manifest.json").read_text())
info = json.loads((HERE / "work" / "wolf_gaits_info.json").read_text())["Trot"]
manifest["clips"]["Trot"] = {
    "label": f"Trot (procedural, gait rollout q5: stride {info['stride']}, {info['seconds']:.4f} s)",
    "duration": info["seconds"], "mode": "loop",
    "provenance": "Procedural trot on the MM9 skeleton (gait_rollout_20261031/q5/scripts/wolf_trot.py): diagonal "
                  "pairs, front R + hind L at phase 0 as Walking; tail lifted over the floor; floor pass applied.",
    "anchors": [{"time": 0, "label": "Trot", "phase": "Start", "source_images": ["../../references_hd/00_three_quarter.png"]}]}
manifest["revision"] = revision
for model in manifest["models"]:
    digest = hashlib.sha256((VIEWER / f"{model['id']}.glb").read_bytes()).hexdigest()
    model.update(revision=revision, sha256=digest, url=f"{model['id']}.glb?v={digest[:12]}")
(VIEWER / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
print("manifest", revision, [m["sha256"][:12] for m in manifest["models"]])
