#!/usr/bin/env python3
"""Measured stride of every walk, run and sprint clip of a world's 3D actor bindings, against
`animation.stride_length`, `run_stride_length` and `sprint_stride_length` in actors.yml.

The engine advances a locomotion clip by the distance the body travels: one loop per stride (ActorModelPresentation.h).
A clip is authored in place, so whatever touches the floor while planted (a foot, paw or spike) slides backwards at the
ground speed the clip was made for. The audit samples each clip, takes the vertices on the floor in two consecutive
samples, and measures their backward speed (the median over all of them); that speed times the clip length is the
stride the binding should carry. When the model has foot joints (names in FOOT), only the vertices they dominate
count, so a robe hem or tail dragging on the floor does not dilute the measurement. Fliers and swimmers (a
`gait_rate` minimum above 0) are left out. A binding stride that differs makes the planted feet slide in game:
longer than measured, they skate forwards; shorter, backwards.

A second, independent measurement tracks the foot joints themselves (the leaf-most joints named in FOOT): their backward
speed while each is in the lowest 15 % of its height range. It reads robed bodies well (the hem around the feet is on
the floor but does not travel) but underestimates runs (its band takes in swing frames near the ground), while the
vertex measurement is the reverse. A measurement is trusted only when the two agree within AGREE.

    stride_audit.py [--world mm8] [--match <descriptor glob>] [--tolerance 0.1]

Reported per model and clip: the measured stride (model units per loop), the share of samples with floor contact, the
foot-joint stride, and each different binding stride with its ratio to the measurement. Flags (<<) a trusted
measurement with a binding ratio outside 1 +- tolerance; marks (??) an untrusted one that neither measurement supports
(a binding within tolerance of either is left alone), for review by eye. A clip without enough floor contact (a
hovering body) is reported as unmeasured. Exits non-zero when any is flagged.
"""
import argparse
import fnmatch
from pathlib import Path
import sys

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import floor_audit  # noqa: E402
import glb_pose  # noqa: E402

ROOT = floor_audit.ROOT
SAMPLES_PER_SECOND = 60
# A vertex is on the floor when it is within this share of the model's height of y = 0.
CONTACT_BAND = 0.015
# Fewer contact samples than this share of the clip leave it unmeasured.
MIN_CONTACT = 0.15
FOOT = ("foot", "toe", "ankle", "hoof", "paw", "tarsus")
# The vertex and foot-joint measurements are trusted when they differ by at most this share.
AGREE = 0.12


def measure(model, clip):
    """(stride in model units per loop, share of samples with floor contact), or (None, share)."""
    duration = model.clip_times(clip)[-1]
    count = max(int(round(duration * SAMPLES_PER_SECOND)), 8)
    times = np.linspace(0.0, duration, count + 1)
    names = [node.get("name", "").lower() for node in model.glb.json["nodes"]]
    feet = np.concatenate([
        np.array([any(part in names[model.joints[joint]] for part in FOOT) for joint in
                  primitive["joints"][np.arange(len(primitive["positions"])), np.argmax(primitive["weights"], axis=1)]],
                 dtype=bool) if primitive["skinned"] else np.zeros(len(primitive["positions"]), dtype=bool)
        for primitive in model.primitives])
    frames, shown = [], []
    for time in times:
        posed = model.skinned_positions(model.world(model.sample(clip, time)))
        frames.append(np.concatenate([points for points, _ in posed]))
        mask = [np.zeros(len(points), dtype=bool) for points, _ in posed]
        for flags, visible in zip(mask, model.visible_vertices(posed)):
            flags[visible] = True
        shown.append(np.concatenate(mask))
    height = max(float(np.ptp(frames[0][shown[0], 1])), 1e-6)
    band = CONTACT_BAND * height
    considered = feet if feet.any() else np.ones(len(feet), dtype=bool)
    velocities, contact = [], 0
    step = duration / count
    for before, after, shown_before, shown_after in zip(frames, frames[1:], shown, shown[1:]):
        planted = considered & shown_before & shown_after & (before[:, 1] < band) & (after[:, 1] < band)
        if planted.any():
            contact += 1
            velocities.append((after[planted][:, [0, 2]] - before[planted][:, [0, 2]]) / step)
    share = contact / count
    if share < MIN_CONTACT:
        return None, share
    velocities = np.concatenate(velocities)
    backward = np.median(velocities, axis=0)
    if np.linalg.norm(backward) < 1e-9:
        return 0.0, share
    direction = backward / np.linalg.norm(backward)
    return float(np.median(velocities @ direction) * duration), share


def measure_feet(model, clip):
    """Stride from the foot joints' own backward speed while low (median over the feet), or None without foot joints."""
    duration = model.clip_times(clip)[-1]
    count = max(int(round(duration * SAMPLES_PER_SECOND * 2)), 16)
    nodes = model.glb.json["nodes"]
    is_foot = [any(part in node.get("name", "").lower() for part in FOOT) for node in nodes]
    feet = [joint for joint in model.joints
            if is_foot[joint] and not any(is_foot[child] for child in nodes[joint].get("children", []))]
    if not feet:
        return None
    positions = np.array([model.world(model.sample(clip, time))[feet][:, :3, 3]
                          for time in np.linspace(0.0, duration, count + 1)])
    strides = []
    for foot in range(len(feet)):
        height = positions[:, foot, 1]
        low = height < height.min() + 0.15 * max(float(np.ptp(height)), 1e-6)
        planted = low[:-1] & low[1:]
        if planted.sum() < 2:
            continue
        travel = positions[:, foot][:, [0, 2]]
        velocities = ((travel[1:] - travel[:-1]) / (duration / count))[planted]
        backward = np.median(velocities, axis=0)
        norm = np.linalg.norm(backward)
        strides.append(0.0 if norm < 1e-9 else float(np.median(velocities @ (backward / norm)) * duration))
    return float(np.median(strides)) if strides else None


def audit(world, match, tolerance, actors=None):
    """actors: the bindings to judge in place of the world's actors.yml (a model path may be absolute)."""
    actors = actors or yaml.safe_load((ROOT / f"assets_dev/worlds/{world}/models/actors.yml").read_text())["actors"]
    models, clips = {}, {}
    for actor in actors:
        animation = actor.get("animation") or {}
        if (match and not fnmatch.fnmatch(actor["descriptor"], match)) or "stride_length" not in animation \
                or animation.get("gait_rate", [0, 0])[0] > 0:
            continue  # unmatched, not animated by distance, or a flier or swimmer
        walk_stride = float(animation["stride_length"])
        run_stride = float(animation.get("run_stride_length", walk_stride * 1.55))
        gaits = [(actor["clips"]["walking"], walk_stride), (animation["run"], run_stride)]
        if "sprint" in animation:
            gaits.append((animation["sprint"], float(animation["sprint_stride_length"])))
        for clip, stride in gaits:
            clips.setdefault((actor["model"], clip), {}).setdefault(round(stride, 4), []).append(actor["descriptor"])
    results = []
    for (path, clip), strides in clips.items():
        model = models.setdefault(path, glb_pose.Model(glb_pose.Glb(ROOT / "assets_source" / path)))
        measured, share = measure(model, clip)
        feet = measure_feet(model, clip)
        trusted = bool(measured and feet and abs(feet / measured - 1.0) <= AGREE)
        bindings = [{"stride": stride, "ratio": stride / measured if measured else None, "descriptors": names}
                    for stride, names in sorted(strides.items())]

        def off(stride, value):
            return not value or abs(stride / value - 1.0) > tolerance

        flagged = trusted and any(off(binding["stride"], measured) for binding in bindings)
        doubtful = not trusted and (measured is not None or feet is not None) and any(
            off(binding["stride"], measured) and off(binding["stride"], feet) for binding in bindings)
        results.append({"model": path, "clip": clip, "measured": measured, "contact": share, "feet": feet,
                        "trusted": trusted, "bindings": bindings, "flagged": flagged, "doubtful": doubtful})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match")
    parser.add_argument("--tolerance", type=float, default=0.1)
    args = parser.parse_args()
    results = audit(args.world, args.match, args.tolerance)
    for result in results:
        measured = "unmeasured" if result["measured"] is None else f"{result['measured']:.3f}"
        cells = "  ".join(f"{binding['stride']:.3f}" + (f" x{binding['ratio']:.2f}" if binding["ratio"] else "")
                          + f" ({binding['descriptors'][0]}" + (f" +{len(binding['descriptors']) - 1}"
                                                               if len(binding["descriptors"]) > 1 else "") + ")"
                          for binding in result["bindings"])
        feet = "-" if result["feet"] is None else f"{result['feet']:.3f}"
        print(f"{Path(result['model']).name[:26]:26} {result['clip'][:18]:18} measured {measured:>10} "
              f"contact {result['contact']:4.0%} feet {feet:>6}  binding {cells}"
              + ("  <<" if result["flagged"] else "  ??" if result["doubtful"] else ""))
    flagged = [result for result in results if result["flagged"]]
    doubtful = [result for result in results if result["doubtful"]]
    print(f"\n{len(results)} clips, {len(flagged)} flagged (trusted measurement, binding off by more than "
          f"{args.tolerance:.0%}), {len(doubtful)} to review (measurements disagree and support neither)")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
