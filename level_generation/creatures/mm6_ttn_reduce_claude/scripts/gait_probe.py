#!/usr/bin/env python3
"""Numbers for a derived walk against its source: knee flexion and direction (a knee must bend forward), the largest
world rotation step per second of every joint (jerk), the loop seam, and the planted feet's lowest vertex.

    gait_probe.py <glb> <clip> [<clip> ...]
"""
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402


def angle(a, b):
    return np.degrees(2 * np.arccos(min(abs(float(np.dot(a, b))), 1.0)))


def main():
    model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
    nodes = model.glb.json["nodes"]
    names = {node.get("name"): i for i, node in enumerate(nodes)}
    legs = [(t, c, f) for t, c, f in (("LeftUpLeg", "LeftLeg", "LeftFoot"), ("RightUpLeg", "RightLeg", "RightFoot"),
                                      ("B_L_Thigh", "B_L_Calf", "B_L_Foot"), ("B_R_Thigh", "B_R_Calf", "B_R_Foot"))
            if t in names]
    for clip in sys.argv[2:]:
        times = model.clip_times(clip)
        length = times[-1]
        count = int(round(length * 60))
        samples = np.linspace(0, length, count + 1)
        worlds = [model.world(model.sample(clip, t)) for t in samples]
        quats = [[glb_pose.matrix_quaternion(w[j][:3, :3]) for j in model.joints] for w in worlds]
        steps = np.array([[angle(a, b) for a, b in zip(q0, q1)] for q0, q1 in zip(quats, quats[1:])]) * (count / length)
        worst = np.argsort(steps.max(axis=0))[::-1][:4]
        seam = max(angle(a, b) for a, b in zip(quats[0], quats[-1]))
        flex, backward = [], 0
        for t, c, f in legs:
            for w in worlds:
                hip, knee, ankle = (w[names[n]][:3, 3] for n in (t, c, f))
                u, v = knee - hip, ankle - knee
                flex.append(np.degrees(np.arccos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
                line = (ankle - hip) / np.linalg.norm(ankle - hip)
                offset = (knee - hip) - np.dot(knee - hip, line) * line
                if np.linalg.norm(offset) > 0.01 and offset[2] < -0.3 * np.linalg.norm(offset):
                    backward += 1
        print(f"{clip}: {length:.3f} s, knee flexion {min(flex):.0f}-{max(flex):.0f} deg, knees pointing backward "
              f"{backward}, loop seam {seam:.2f} deg, fastest joints (deg/s): " + ", ".join(
                  f"{nodes[model.joints[j]]['name']} {steps[:, j].max():.0f}" for j in worst))


if __name__ == "__main__":
    main()
