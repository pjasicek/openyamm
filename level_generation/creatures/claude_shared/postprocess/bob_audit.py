#!/usr/bin/env python3
"""Head bob of every grounded biped's walk and run clip in a world's actors.yml bindings.

The bob is the head joint's peak-to-peak height over the loop, in per cent of its standing height (Standing at 0 s).
A biped is a model with exactly two leaf foot joints (FOOT names, as in stride_audit.py) and a head joint; fliers and
swimmers (a `gait_rate` minimum above 0) and `z_offset` bindings are left out. Across MM6-MM8 after the 2026-10-22
pass walks sit near 3-5 % and runs near 4-7 %; people bob about 2.5-3 % walking and 4-6 % running.

    bob_audit.py [--world mm8] [--match <model glob>]

Per model and clip: the bob, the share of it carried by the pelvis, and `uneven` (the first harmonic, once per loop,
over the second, once per step: above about 0.6 one step rises higher than the other). Flags a walk outside
WALK and a run outside RUN. Fix with bob_fix.py (see level_generation/creatures/head_bob_claude/).
"""
import argparse
import fnmatch
from pathlib import Path
import sys

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import bob_fix  # noqa: E402
import floor_audit  # noqa: E402
import glb_pose  # noqa: E402

ROOT = floor_audit.ROOT
WALK = (2.0, 6.5)
RUN = (3.0, 8.5)


def measure(model, clip, head, pelvis, height):
    duration = model.clip_times(clip)[-1]
    times = np.linspace(0.0, duration, max(int(duration * 120), 48), endpoint=False)
    heights = np.array([[pose[head][1, 3], pose[pelvis][1, 3]]
                        for pose in (model.world(model.sample(clip, time)) for time in times)])
    spectrum = np.abs(np.fft.rfft(heights[:, 0] - heights[:, 0].mean()))
    return {"bob": float(np.ptp(heights[:, 0]) / height * 100.0),
            "pelvis": float(np.ptp(heights[:, 1]) / max(np.ptp(heights[:, 0]), 1e-9)),
            "uneven": float(spectrum[1] / max(spectrum[2], 1e-9))}


def audit(world, match):
    actors = yaml.safe_load((ROOT / f"assets_dev/worlds/{world}/models/actors.yml").read_text())["actors"]
    clips = {}
    for actor in actors:
        animation = actor.get("animation") or {}
        if "stride_length" not in animation or animation.get("gait_rate", [0, 0])[0] > 0 or actor.get("z_offset") \
                or (match and not fnmatch.fnmatch(Path(actor["model"]).name, match)):
            continue
        walk = actor["clips"]["walking"]
        clips.setdefault((actor["model"], walk), set()).add("walk")
        clips.setdefault((actor["model"], animation["run"]), set()).add("walk" if animation["run"] == walk else "run")
    models, results = {}, []
    for (path, clip), kinds in clips.items():
        model = models.setdefault(path, glb_pose.Model(glb_pose.Glb(ROOT / "assets_source" / path)))
        try:
            head = bob_fix.find_joint(model, "head")
            bob_fix.legs(model)
        except SystemExit:
            continue  # not a biped
        stand = "Standing" if "Standing" in model.clips else clip
        height = float(model.world(model.sample(stand, 0.0))[head][1, 3])
        kind = "walk" if "walk" in kinds else "run"
        result = measure(model, clip, head, model.root_joints[0], height)
        low, high = WALK if kind == "walk" else RUN
        results.append({"model": path, "clip": clip, "kind": kind, **result,
                        "flagged": not low <= result["bob"] <= high})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match")
    args = parser.parse_args()
    results = sorted(audit(args.world, args.match), key=lambda result: -result["bob"])
    for result in results:
        print(f"{Path(result['model']).name[:26]:26} {result['clip'][:14]:14} {result['kind']:4} "
              f"bob {result['bob']:5.1f}%  pelvis share {result['pelvis']:4.2f}  uneven {result['uneven']:5.2f}"
              + ("  <<" if result["flagged"] else ""))
    flagged = [result for result in results if result["flagged"]]
    print(f"\n{len(results)} clips, {len(flagged)} outside walk {WALK[0]}-{WALK[1]} % / run {RUN[0]}-{RUN[1]} %")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
