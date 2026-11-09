#!/usr/bin/env python3
"""Quick numbers for added script clips (2026-10-31 dropped-clip pass), per clip at FPS on the LOD0 mesh:

- floor: lowest visible point per frame (cm in model metres): min, max, and the first and last frame;
- bones: limb joints (Thigh, Calf, UpperArm, Forearm, Foot, Hand) whose posed parent-to-child length differs from
  rest by over 10 %, worst ratio;
- jitter: the skinned vertices' second difference per frame (mm/frame^2), p99 over vertices, worst frame; with a
  reference GLB (the same clip before corrections) also the reference's worst, so a correction that shakes shows up.

    new_clip_measure.py <glb> <Clip1,Clip2,...> [--ref <glb>] [--fps 30] [--json out.json]
"""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402

LIMB = re.compile(r'(Thigh|Calf|UpperArm|Forearm|Foot|Hand)$')


def frames(model, clip, fps):
    times = model.clip_times(clip)
    n = max(2, int(round((times[-1] - times[0]) * fps)) + 1)
    return np.linspace(times[0], times[-1], n)


def measure(model, clip, fps):
    nodes = model.glb.json['nodes']
    limbs = [j for j in model.joints if LIMB.search(nodes[j].get('name', ''))]
    rest_len = {j: float(np.linalg.norm(model.rest[j][0])) for j in limbs}
    lows, verts, worst_bone = [], [], (1.0, '')
    for t in frames(model, clip, fps):
        local = model.sample(clip, float(t))
        world = model.world(local)
        posed = model.skinned_positions(world)
        visible = model.visible_vertices(posed)
        lows.append(min(float(p[v, 1].min()) for (p, _), v in zip(posed, visible) if len(v)))
        verts.append(np.concatenate([p for p, _ in posed]))
        for j in limbs:
            if rest_len[j] < 1e-4:
                continue
            length = float(np.linalg.norm(local[j][0] if j in local else model.rest[j][0]))
            ratio = length / rest_len[j]
            off = max(ratio, 1 / max(ratio, 1e-6))
            if off > worst_bone[0]:
                worst_bone = (off, nodes[j].get('name'))
    V = np.stack(verts)
    acc = np.linalg.norm(V[2:] - 2 * V[1:-1] + V[:-2], axis=2) * 1000 if len(V) > 2 else np.zeros((1, 1))
    p99 = np.percentile(acc, 99, axis=1)
    lows = np.array(lows) * 100
    return {'frames': len(V), 'floor_min_cm': round(float(lows.min()), 2), 'floor_max_cm': round(float(lows.max()), 2),
            'floor_first_last_cm': [round(float(lows[0]), 2), round(float(lows[-1]), 2)],
            'bone_worst_ratio': round(worst_bone[0], 3), 'bone_worst_joint': worst_bone[1],
            'bones_over_10pct': worst_bone[0] > 1.1,
            'jitter_p99_mm_f2': round(float(p99.max()), 2), 'jitter_frame': int(p99.argmax()) + 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('glb', type=Path)
    parser.add_argument('clips')
    parser.add_argument('--ref', type=Path)
    parser.add_argument('--fps', type=float, default=30.0)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    model = glb_pose.Model(glb_pose.Glb(args.glb))
    ref = glb_pose.Model(glb_pose.Glb(args.ref)) if args.ref else None
    out = {}
    for clip in args.clips.split(','):
        r = measure(model, clip, args.fps)
        if ref is not None and clip in ref.clips:
            r['ref_jitter_p99_mm_f2'] = measure(ref, clip, args.fps)['jitter_p99_mm_f2']
        out[clip] = r
        print(clip, json.dumps(r), flush=True)
    if args.json:
        json.dump(out, open(args.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
