#!/usr/bin/env python3
"""Lowest point of a GLB clip over its loop: per sampled time the lowest LOD0 vertex (glTF y, cm of model units) and
the joint that weighs most on it, to see which part dips under the floor (floor_audit.py only gives the depth).

    low_probe.py <glb> <clip> [samples]
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    clip = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    names = [glb.json["nodes"][j].get("name") for j in model.joints]
    duration = model.clip_times(clip)[-1]
    for k in range(count):
        t = k * duration / count
        posed = model.skinned_positions(model.world(model.sample(clip, t)))
        best = None
        for (points, _), primitive in zip(posed, model.primitives):
            i = int(np.argmin(points[:, 1]))
            if best is None or points[i, 1] < best[0]:
                joint = names[primitive["joints"][i][int(np.argmax(primitive["weights"][i]))]] \
                    if primitive["skinned"] else "-"
                best = (float(points[i, 1]), joint, points[i])
        print(f"{clip} {k / count:.3f}  lowest {best[0] * 100:+6.2f} cm  {best[1]:14}  "
              f"at x {best[2][0]:+.3f} z {best[2][2]:+.3f}")


if __name__ == "__main__":
    main()
