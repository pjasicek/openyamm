#!/usr/bin/env python3
"""Skirt vertices inside the leg capsules (h04; the measure compose_gait.py's clear_skirt works on): lower half of the
thigh and knee to ankle, radii 0.065 / 0.055 m. Per clip: share of samples with a vertex deeper than 3 mm, the deepest
(mm), and per sample (12 phases) the deepest chain, its depth and height. Compare new clips with the accepted ones.

    skirt_capsule_probe.py <glb> <clip>[,<clip>...] [--prefix Skirt_] [--detail]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

RADIUS = {'Thigh': 0.065, 'Calf': 0.055}


def main():
    args = sys.argv[1:]
    prefix = args[args.index('--prefix') + 1] if '--prefix' in args else 'Skirt_'
    glb = glb_pose.Glb(args[0])
    model = glb_pose.Model(glb)
    names = [n.get('name', '') for n in glb.json['nodes']]
    I = {n: i for i, n in enumerate(names)}
    prim = model.primitives[0]
    dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    si = np.array([i for i, d in enumerate(dom) if d.startswith(prefix)])
    chain = np.array([dom[v][len(prefix):].rsplit('_', 1)[0] for v in si])
    for clip in args[1].split(','):
        T = model.clip_times(clip)[-1]
        times = np.arange(0, T, 1 / 60)
        rows, hits, worst = [], 0, 0.0
        for t in times:
            W = model.world(model.sample(clip, float(t)))
            pts = model.skinned_positions(W)[0][0][si]
            best = np.zeros(len(si))
            for s in 'LR':
                H, K, A = (W[I[f'B_{s}_{b}'], :3, 3] for b in ('Thigh', 'Calf', 'Foot'))
                for seg, (a, b) in (('Thigh', (0.5 * (H + K), K)), ('Calf', (K, A))):
                    ab = b - a
                    u = np.clip(((pts - a) @ ab) / (ab @ ab), 0, 1)
                    best = np.maximum(best, RADIUS[seg] - np.linalg.norm(pts - (a + u[:, None] * ab), axis=1))
            k = int(np.argmax(best))
            if best[k] > 0.003:
                hits += 1
            worst = max(worst, best[k])
            rows.append((t / T, best[k], chain[k], pts[k][1]))
        print(f'{clip:10} skirt inside legs: {100 * hits / len(times):.0f}% max {1000 * worst:.0f} mm')
        if '--detail' in args:
            for ph, d, c, y in rows[::max(1, len(rows) // 12)]:
                print(f'   {ph:.2f} {1000 * d:4.0f} mm chain {c} y {y:.2f}')


if __name__ == '__main__':
    main()
