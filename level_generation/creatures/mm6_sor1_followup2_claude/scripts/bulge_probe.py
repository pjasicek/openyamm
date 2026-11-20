#!/usr/bin/env python3
"""Robe hip bulge: the robe's sideways half-width (|x| about the pelvis, the bodies face +Z, left +X) in height bands,
per clip, against Standing's first frame. Robe vertices are those dominated by a Robe_* bone.

    bulge_probe.py <glb> [clip,...]      prints per band: Standing rest, clip mean and max (cm), and max - rest
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

BANDS = [(0.95, 1.05), (0.85, 0.95), (0.75, 0.85), (0.6, 0.75), (0.4, 0.6), (0.2, 0.4)]


def widths(model, prims, robe, pelvis, clip, t):
    W = model.world(model.sample(clip, t))
    px = W[pelvis][0, 3]
    out = []
    pts_all = []
    for (pts, _), mask in zip(model.skinned_positions(W), robe):
        if mask.any():
            pts_all.append(pts[mask])
    P = np.vstack(pts_all)
    floor = 0.0
    for lo, hi in BANDS:
        sel = (P[:, 1] - floor >= lo) & (P[:, 1] - floor < hi)
        if not sel.any():
            out.append((np.nan, np.nan))
            continue
        x = P[sel, 0] - px
        out.append((x.max(), -x.min()))           # left, right half-widths
    return np.array(out)


def main():
    glb = open_glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    pelvis = names.index('B_Pelvis')
    robe = []
    for prim in model.primitives:
        j = prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]
        robe.append(np.array([names[model.joints[k]].startswith('Robe_') for k in j]))
    clips = sys.argv[2].split(',') if len(sys.argv) > 2 else ['Walking', 'Jog']
    rest = widths(model, None, robe, pelvis, 'Standing', 0.0)
    print('band (m)      ' + ' '.join(f'{lo:.2f}-{hi:.2f}'.rjust(11) for lo, hi in BANDS))
    print('Standing L/R  ' + ' '.join(f'{100 * a:5.1f}/{100 * b:4.1f}' for a, b in rest))
    for clip in clips:
        T = model.clip_times(clip)[-1]
        n = 40
        allw = np.array([widths(model, None, robe, pelvis, clip, k * T / n) for k in range(n)])
        mean = allw.mean(axis=0)
        mx = allw.max(axis=0)
        print(f'{clip:9} mean ' + ' '.join(f'{100 * a:5.1f}/{100 * b:4.1f}' for a, b in mean))
        print(f'{clip:9} max  ' + ' '.join(f'{100 * a:5.1f}/{100 * b:4.1f}' for a, b in mx))
        print(f'{clip:9} +max ' + ' '.join(f'{100 * (a - r[0]):5.1f}/{100 * (b - r[1]):4.1f}' for (a, b), r in zip(mx, rest)))


if __name__ == '__main__':
    main()
