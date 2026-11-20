#!/usr/bin/env python3
"""Arm and hand numbers of walk clips (the humanoid playbook's arm and hand gate, without Blender): per side, the
wrist bend (hand against forearm, from the rest relation), the forearm and upper-arm roll about their own axis, and
the smallest distance from the forearm and hand vertices to the torso, pelvis and thigh vertices (an arm swinging into
the body shows as a distance near zero). Compare a derived clip with its source.

    gait_arms.py <glb> <config.json> <clip> [<clip> ...]
"""
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402


def relative(world, rest_world, parent, child):
    """Rotation of child against parent, relative to their rest relation (degrees, and roll about the child axis)."""
    now = np.linalg.inv(world[parent][:3, :3]) @ world[child][:3, :3]
    rest = np.linalg.inv(rest_world[parent][:3, :3]) @ rest_world[child][:3, :3]
    delta = now @ rest.T
    angle = np.degrees(np.arccos(np.clip((np.trace(delta) - 1) / 2, -1, 1)))
    return angle


def main():
    model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
    config = json.loads(Path(sys.argv[2]).read_text())["joints"]
    names = {node.get("name"): i for i, node in enumerate(model.glb.json["nodes"])}
    rest_world = model.world({})
    body_names = [config["pelvis"], *config["spine"], config["left"]["thigh"], config["right"]["thigh"]]
    body_nodes = {names[n] for n in body_names}
    for clip in sys.argv[3:]:
        length = model.clip_times(clip)[-1]
        count = int(round(length * 30))
        row = []
        for side in ("left", "right"):
            arm = [names[n] for n in config[side]["arm"]]
            forearm = [n for n in config[side]["arm"] if "fore" in n.lower()][0]
            hand = [n for n in config[side]["arm"] if "hand" in n.lower()][0]
            limb_nodes = {names[forearm], names[hand]} | {i for n, i in names.items()
                                                          if n.startswith(hand.replace("Hand", "Finger"))}
            masks = []
            for primitive in model.primitives:
                dominant = np.array([model.joints[j] for j in primitive["joints"][
                    np.arange(len(primitive["positions"])), np.argmax(primitive["weights"], axis=1)]])
                masks.append((np.isin(dominant, list(limb_nodes)), np.isin(dominant, list(body_nodes))))
            wrist, upper, clearance = 0.0, 0.0, np.inf
            for k in range(count):
                world = model.world(model.sample(clip, length * k / count))
                wrist = max(wrist, relative(world, rest_world, names[forearm], names[hand]))
                upper = max(upper, relative(world, rest_world, arm[0], arm[1]))
                posed = model.skinned_positions(world)
                limb = np.concatenate([p[a] for (p, _), (a, _) in zip(posed, masks)])[::2]
                body = np.concatenate([p[b] for (p, _), (_, b) in zip(posed, masks)])[::3]
                distance = np.sqrt(((limb[:, None, :] - body[None, :, :]) ** 2).sum(axis=2)).min()
                clearance = min(clearance, distance)
            row.append(f"{side}: wrist <= {wrist:.0f} deg, upper arm vs clavicle <= {upper:.0f} deg, "
                       f"forearm/hand to body >= {clearance * 100:.1f} cm")
        print(f"{clip}: " + "; ".join(row))


if __name__ == "__main__":
    main()
