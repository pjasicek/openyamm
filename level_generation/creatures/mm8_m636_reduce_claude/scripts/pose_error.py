#!/usr/bin/env python3
"""Surface distance between the source school and a candidate at every 3rd dumped frame (pose_dump.py, 24 Hz) of
every clip: exact point-to-triangle distance from each surface's vertices and face centres to the other surface
(each fish against its own copy), both directions, divided by the fish's scale (Fish00 units). Limits as the
playbook's (p99 0.3 %, max 1.5 % of the model size): per fish from Fish00's 0.765 m length (2.3 / 11.5 mm), and
in world units for the whole school as one actor (2.0 m bound: 6.0 / 30 mm).
Usage: pose_error.py <src label> <cand label> [...] -> prints, work/err_<cand>.json"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fish_build import closest_on_tris  # noqa: E402
W = Path(__file__).resolve().parents[1] / 'work'; S = np.load(W / 'fish.npz')['S']
L = 0.765; P99, MAX = 0.003 * L, 0.015 * L
LW = 2.0; P99W, MAXW = 0.003 * LW, 0.015 * LW


def dist(points, P, T):
    a, b, c = (P[T[:, k]].astype(np.float64) for k in range(3)); out = np.empty(len(points))
    for i in range(0, len(points), 256):
        q = points[i:i + 256].astype(np.float64); B = closest_on_tris(q, a, b, c)
        X = np.einsum('qtk,tkc->qtc', B, np.stack([a, b, c], 1)); out[i:i + 256] = np.linalg.norm(X - q[:, None], axis=-1).min(1)
    return out


if __name__ == '__main__':
    src = np.load(W / f'pose_{sys.argv[1]}.npz')
    for lab in sys.argv[2:]:
        cand = np.load(W / f'pose_{lab}.npz'); worst = []
        for key in [k for k in src.files if k.startswith('clip_')]:
            for fr in range(0, len(src[key]), 3):
                for k in range(12):
                    st = src['tris'][src['fish'][src['tris'][:, 0]] == k]; ct = cand['tris'][cand['fish'][cand['tris'][:, 0]] == k]
                    A, B = src[key][fr], cand[key][fr]
                    qa = np.r_[A[np.unique(st)], A[st].mean(1)]; qb = np.r_[B[np.unique(ct)], B[ct].mean(1)]
                    da, db = dist(qa, B, ct) / S[k], dist(qb, A, st) / S[k]; d = np.r_[da, db]
                    dw = d * S[k]
                worst.append((float(np.percentile(d, 99)), float(d.max()), float(np.percentile(dw, 99)), float(dw.max()),
                              key[5:], fr, k, 'src->cand' if da.max() >= db.max() else 'cand->src'))
        w = np.array([x[:4] for x in worst]); i99, imax = w[:, 0].argmax(), w[:, 1].argmax()
        mm = lambda x: round(float(x) * 1000, 2)
        res = {'fish_p99_mm': mm(w[:, 0].max()), 'fish_max_mm': mm(w[:, 1].max()), 'median_frame_p99_mm': mm(np.median(w[:, 0])),
               'p99_at': worst[i99][4:], 'max_at': worst[imax][4:], 'pass_per_fish': bool(w[:, 0].max() <= P99 and w[:, 1].max() <= MAX),
               'world_p99_mm': mm(w[:, 2].max()), 'world_max_mm': mm(w[:, 3].max()),
               'pass_school': bool(w[:, 2].max() <= P99W and w[:, 3].max() <= MAXW)}
        json.dump(res, open(W / f'err_{lab}.json', 'w'))
        print(lab, res, flush=True)
