#!/usr/bin/env python3
"""Close the seam of looping clips, in a copy of a GLB (anim fixes, 2026-11-11).

    loop_close.py <in.glb> <out.glb> --clips Running [Walking ...] [--window 1.0] [--min-deg 0.5]

A loop whose last key differs from its first jumps when the engine wraps. Per rotation channel whose last and first
values differ by more than --min-deg (and per translation channel by more than 1 mm), the difference is spread over
the clip's last --window share (1.0: the whole clip, linearly; less: a smoothstep ramp over that tail), so the last key
lands exactly on the first and the motion before the ramp is untouched. Only the matched samplers' outputs change.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def qmul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clips', nargs='+', required=True)
    p.add_argument('--window', type=float, default=1.0)
    p.add_argument('--min-deg', type=float, default=0.5)
    args = p.parse_args()
    g = glb_pose.Glb(args.input)
    doc = g.json
    names = {a.get('name'): i for i, a in enumerate(doc['animations'])}
    nodes = doc['nodes']
    for clip in args.clips:
        anim = doc['animations'][names[clip]]
        fixed = []
        for ch in anim['channels']:
            path = ch['target']['path']
            if path not in ('rotation', 'translation'):
                continue
            sampler = anim['samplers'][ch['sampler']]
            t = g.accessor(sampler['input'])[:, 0].astype(np.float64)
            v = g.accessor(sampler['output']).astype(np.float64)
            if len(t) < 3:
                continue
            u = (t - t[0]) / max(t[-1] - t[0], 1e-9)
            if args.window >= 1.0:
                w = u
            else:
                x = np.clip((u - (1 - args.window)) / args.window, 0, 1)
                w = x * x * (3 - 2 * x)
            if path == 'rotation':
                q0 = v[0] / np.linalg.norm(v[0])
                q1 = v[-1] / np.linalg.norm(v[-1])
                if np.dot(q0, q1) < 0:
                    q1 = -q1
                ang = np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(q0, q1))))))
                if ang < args.min_deg:
                    continue
                corr = qmul(q0, qinv(q1))                     # world-left correction taking the end to the start
                out = []
                for k in range(len(v)):
                    c = glb_pose.slerp(np.array([0.0, 0.0, 0.0, 1.0]), corr, float(w[k]))
                    q = qmul(c, v[k] / np.linalg.norm(v[k]))
                    out.append(q / np.linalg.norm(q))
                out = np.array(out)
                for k in range(1, len(out)):
                    if np.dot(out[k], out[k - 1]) < 0:
                        out[k] = -out[k]
                out[-1] = out[0] if np.dot(out[0], out[-1]) > 0 else -out[0]
                kind = 'VEC4'
            else:
                d = v[0] - v[-1]
                if np.linalg.norm(d) < 0.001:
                    continue
                ang = float(np.linalg.norm(d))
                out = v + w[:, None] * d[None, :]
                kind = 'VEC3'
            sampler['output'] = g.append_accessor(out, kind)
            fixed.append((nodes[ch['target']['node']].get('name'), path, round(ang, 3)))
        print(f'LOOPCLOSE {clip}: {len(fixed)} channels', sorted(fixed, key=lambda x: -x[2])[:6])
    g.write(args.output)


if __name__ == '__main__':
    main()
