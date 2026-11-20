#!/usr/bin/env python3
"""Same-side paw clearance of the MM9 wolf's locomotion clips: per sample, the smallest distance between the skin of the
front foot (Bone13/Bone19, Bone18/Bone05) and the hind foot (Bone03/Bone09, Bone08/Bone42) on each side (a trot's hind
paw lands where the front paw lifts: overreach must not run through it). Model units.

    paw_clash.py <glb> <clip>[,<clip>...]
"""
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402

PAIRS = {"left": (("Bone13", "Bone19"), ("Bone03", "Bone09")), "right": (("Bone18", "Bone05"), ("Bone08", "Bone42"))}
g = glb_pose.Glb(sys.argv[1]); m = glb_pose.Model(g)
joints = [g.json["nodes"][j].get("name") for j in m.joints]
prim = m.primitives[0]
dom = np.array([joints[prim["joints"][v][int(np.argmax(prim["weights"][v]))]] for v in range(len(prim["weights"]))])
for clip in sys.argv[2].split(","):
    T = m.clip_times(clip)[-1]
    for side, (front, hind) in PAIRS.items():
        best, inside = (9.0, 0.0), (0, 0.0)
        for k in range(48):
            pos = m.skinned_positions(m.world(m.sample(clip, k * T / 48)))[0][0]
            d = cKDTree(pos[np.isin(dom, front)]).query(pos[np.isin(dom, hind)])[0].min()
            best = min(best, (float(d), k / 48))
            n = int((Delaunay(pos[np.isin(dom, (front[1],))]).find_simplex(pos[np.isin(dom, hind)]) >= 0).sum())
            inside = max(inside, (n, k / 48))
        print(f"{clip:8} {side:5} closest front/hind foot skin {best[0] * 100:5.1f} cm at phase {best[1]:.2f}; "
              f"hind foot vertices inside the front paw's hull: {inside[0]} at {inside[1]:.2f}")
