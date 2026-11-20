#!/usr/bin/env python3
"""Footfall, duty, head bob and planted paw heading of the MM9 wolf's locomotion clips (MM9 bone names), for comparing
a new clip with the installed Walking and Running (q3's quad_probe.py reads rat-route names).

Per clip: the Bone27 (skull) bob, peak-to-peak in % of its Standing height; per paw joint (Bone19 front L, Bone05
front R, Bone09 hind L, Bone42 hind R) the touchdown phase (first sample of the stance after a swing) and the
lift-off, the duty (share of the loop planted: the lowest skinned vertex of the paw and the bone above it, within
`--band` model units of its own lowest height over the clip, and moving back; the MM9 hind paws stand about 5 cm
above the floor in Standing), the phase of furthest forward reach,
and the planted heading: the paw joint frame's horizontal heading relative to its Standing frame (degrees, + = toe
out on either side), mean and range while planted. The heading is relative to Standing because the MM9 joints carry
no foot axis (every bone points up).

    wolf_probe.py <glb> <clip>[,<clip>...] [--band 0.03] [--count 120]
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402

PAWS = {"Bone19": "front L", "Bone05": "front R", "Bone09": "hind L", "Bone42": "hind R"}
FOOT = {"Bone19": ("Bone19", "Bone13"), "Bone05": ("Bone05", "Bone18"), "Bone09": ("Bone09", "Bone03"),
        "Bone42": ("Bone42", "Bone08")}          # paw and the bone above it (the skin weighted to them)


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    band = arg("--band", 0.03)
    count = arg("--count", 120)
    index = {node.get("name"): i for i, node in enumerate(glb.json["nodes"])}
    joints = [glb.json["nodes"][j].get("name") for j in model.joints]
    prim = model.primitives[0]
    dominant = np.array([joints[prim["joints"][v][int(np.argmax(prim["weights"][v]))]]
                         for v in range(len(prim["weights"]))])
    stand = model.world(model.sample("Standing", 0.0))
    skull = index["Bone27"]
    height = float(stand[skull][1, 3])
    # forward (+Z in glTF) in each paw's Standing frame
    fwd_local = {p: stand[index[p]][:3, :3].T @ np.array([0.0, 0.0, 1.0]) for p in PAWS}
    for clip in sys.argv[2].split(","):
        duration = model.clip_times(clip)[-1]
        ts = np.arange(count) * duration / count
        worlds = [model.world(model.sample(clip, t)) for t in ts]
        heads = np.array([w[skull][1, 3] for w in worlds])
        spectrum = np.abs(np.fft.rfft(heads - heads.mean()))
        lows = {p: [] for p in PAWS}
        for w in worlds:
            pos = model.skinned_positions(w)[0][0]
            for p in PAWS:
                lows[p].append(pos[np.isin(dominant, FOOT[p])][:, 1].min())
        print(f"{clip:10} {duration:.4f} s  skull bob {np.ptp(heads) / height * 100:4.1f} % "
              f"(1st/2nd harmonic {spectrum[1] / max(spectrum[2], 1e-9):5.2f})  skull mean y {heads.mean():.3f}")
        for p, label in PAWS.items():
            j = index[p]
            z = np.array([w[j][2, 3] for w in worlds])
            vz = (np.roll(z, -1) - np.roll(z, 1)) / (2 * duration / count)
            low = np.array(lows[p])
            planted = (low < low.min() + band) & (vz < 0)
            # touchdown: start of the longest planted run (cyclic)
            runs, start = [], None
            seq = list(planted) + list(planted)
            for k in range(2 * count):
                if seq[k] and start is None:
                    start = k
                if (not seq[k] or k == 2 * count - 1) and start is not None:
                    runs.append((k - start, start % count))
                    start = None
            length, down = max(runs) if runs else (0, 0)
            down_phase = down / count
            up_phase = ((down + min(length, count)) % count) / count
            v = np.array([w[j][:3, :3] @ fwd_local[p] for w in worlds])
            sign = 1.0 if label.endswith("L") else -1.0
            yaw = sign * np.degrees(np.arctan2(v[:, 0], v[:, 2]))
            print(f"    {label:7} {p}: touchdown {down_phase:.2f} lift-off {up_phase:.2f} duty {planted.mean():.2f} "
                  f"furthest forward {int(np.argmax(z)) / count:.2f}  lowest {low.min() * 100:+.2f} cm  "
                  f"planted heading {yaw[planted].mean() if planted.any() else 0:+5.1f} "
                  f"({yaw[planted].min() if planted.any() else 0:+.1f}..{yaw[planted].max() if planted.any() else 0:+.1f})"
                  f"  sweep {np.ptp(z[planted]) if planted.any() else 0:.3f}")


if __name__ == "__main__":
    main()
