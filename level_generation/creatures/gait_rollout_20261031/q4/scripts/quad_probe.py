#!/usr/bin/env python3
"""Head bob and paw heading of a quadruped GLB's locomotion clips (bob_audit.py and foot_heading_probe.py only read
bipeds). Bob: the Head joint's peak-to-peak height over the loop in per cent of its height in Standing at 0 s, and
`uneven` (first harmonic over second, as bob_audit.py). Paw heading: as foot_heading_probe.py, each paw's lateral axis (Standing's
horizontal axis across the paw: up x the paw's long axis, the joint's local +Y, carried in the joint's frame; the axis
the paw pitches about, so it stays defined while the paw points down in the swing) turned into a heading on the
ground, in degrees of toe-out from the direction of travel (positive = toe out, either side), while planted (paw
joint in its lowest 25 %) and its range while swinging.
Also the footfall: the phase at which each paw joint is furthest forward (about its touchdown), to compare clips'
phases.

    quad_probe.py <glb> <clip>[,<clip>...] [--head <joint>] [--paws FL,FR,HL,HR]

(default Head and FrontPaw/HindPaw; the Hydra's middle head is Head3, the Gorgon's paws FrontHoof_L,FrontHoof_R,
HindHoof_L,HindHoof_R)
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402

PAWS = ("FrontPaw_L", "FrontPaw_R", "HindPaw_L", "HindPaw_R")


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    index = {node.get("name"): i for i, node in enumerate(glb.json["nodes"])}
    head = index[sys.argv[sys.argv.index("--head") + 1] if "--head" in sys.argv else "Head"]
    stand = model.world(model.sample("Standing", 0.0))
    height = float(stand[head][1, 3])
    lateral = {}
    paws = sys.argv[sys.argv.index("--paws") + 1].split(",") if "--paws" in sys.argv else PAWS
    for paw in paws:
        d = stand[index[paw]][:3, 1]
        lat = np.cross([0.0, 1.0, 0.0], [d[0], 0.0, d[2]])
        lateral[paw] = stand[index[paw]][:3, :3].T @ (lat / np.linalg.norm(lat))
    for clip in sys.argv[2].split(","):
        duration = model.clip_times(clip)[-1]
        count = 120
        poses = [model.world(model.sample(clip, k * duration / count)) for k in range(count)]
        heads = np.array([pose[head][1, 3] for pose in poses])
        spectrum = np.abs(np.fft.rfft(heads - heads.mean()))
        print(f"{clip:8} {duration:.4f} s  head bob {np.ptp(heads) / height * 100:4.1f} %  "
              f"uneven {spectrum[1] / max(spectrum[2], 1e-9):5.2f}")
        for paw in paws:
            j = index[paw]
            sign = 1.0 if paw.endswith("_L") else -1.0
            # glTF: forward is +Z (Blender -Y), left is +X
            x = np.array([pose[j][:3, :3] @ lateral[paw] for pose in poses])
            yaw = sign * np.degrees(np.arctan2(-x[:, 2], x[:, 0]))   # lateral x up: the paw's heading
            h = np.array([pose[j][1, 3] for pose in poses])
            low = h <= h.min() + 0.25 * max(np.ptp(h), 1e-9)
            forward = np.array([pose[j][2, 3] for pose in poses])
            down = [int(np.argmax(forward)) / count]
            swing = f"swing {yaw[~low].min():+5.1f}..{yaw[~low].max():+5.1f}" if (~low).any() else ""
            print(f"    {paw:10} planted toe-out {yaw[low].mean():+5.1f} ({yaw[low].min():+5.1f}..{yaw[low].max():+5.1f})"
                  f"  {swing}  touchdown at {', '.join(f'{t:.2f}' for t in down)}")


if __name__ == "__main__":
    main()
