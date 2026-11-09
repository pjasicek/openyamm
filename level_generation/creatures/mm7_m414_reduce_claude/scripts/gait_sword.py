#!/usr/bin/env python3
"""Sword clearance of walk clips: the attachment GLB's LOD0 vertices placed on the body's Sword joint, against the
posed body's LOD0 vertices outside the right hand and fingers. Prints per clip the smallest blade-to-body distance and
the frame, with the blade's lowest point (a carried blade must not touch the legs or the floor).

    gait_sword.py <body.glb> <sword.glb> <clip> [<clip> ...]
"""
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402


def main():
    body = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
    sword = glb_pose.Model(glb_pose.Glb(sys.argv[2]))
    names = {node.get("name"): i for i, node in enumerate(body.glb.json["nodes"])}
    blade = np.concatenate([points for points, _ in sword.skinned_positions(sword.world({}))])
    hand_nodes = {i for name, i in names.items() if name.startswith("B_R_Hand") or name.startswith("B_R_Finger")
                  or name in ("Sword", "B_R_ForearmTwist")}
    masks = []
    for primitive in body.primitives:
        dominant = primitive["joints"][np.arange(len(primitive["positions"])), np.argmax(primitive["weights"], axis=1)]
        masks.append(np.array([body.joints[j] not in hand_nodes for j in dominant]))
    for clip in sys.argv[3:]:
        length = body.clip_times(clip)[-1]
        best, low = (np.inf, 0, ""), np.inf
        for k in range(int(round(length * 30))):
            time = length * k / round(length * 30)
            world = body.world(body.sample(clip, time))
            posed = body.skinned_positions(world)
            points = np.concatenate([p[m] for (p, _), m in zip(posed, masks)])
            placed = blade @ world[names["Sword"]][:3, :3].T + world[names["Sword"]][:3, 3]
            low = min(low, placed[:, 1].min())
            distance = np.sqrt(((placed[:, None, :] - points[None, ::3, :]) ** 2).sum(axis=2))
            index = np.unravel_index(np.argmin(distance), distance.shape)
            if distance[index] < best[0]:
                best = (distance[index], time, index[0])
        print(f"{clip}: blade-to-body min {best[0] * 100:.1f} cm at {best[1]:.2f} s, blade lowest {low * 100:.1f} cm")


if __name__ == "__main__":
    main()
