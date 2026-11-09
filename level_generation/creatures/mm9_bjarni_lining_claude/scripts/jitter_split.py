#!/usr/bin/env python3
"""The jitter gate's shoulder-skin statistic split into the installed vertex rows and the appended lining rows (both sides,
every clip, 30 fps as jitter_gate.py): p95 and max of the per-vertex second difference (mm/f^2) over the vertices whose dominant
joint is that side's Clavicle/UpperArm. The lined GLB keeps every installed row, so the installed-row numbers must equal the
installed file's; the lining rows copy their source's joints and weights. Usage: jitter_split.py <installed glb> <lined glb> [clips]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
inst, lined = sys.argv[1:3]; CL = sys.argv[3].split(',') if len(sys.argv) > 3 else None
n0 = [len(p['positions']) for p in Model(Glb(Path(inst))).primitives]
m = Model(Glb(Path(lined))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]) for k in USE])
new = np.concatenate([np.arange(len(P[k]['positions'])) >= n0[k] for k in USE])
for clip in m.clips:
    if CL and clip not in CL:
        continue
    ts = np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30)
    X = np.array([np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k in USE]) for t in ts])
    A = np.linalg.norm(X[2:] - 2 * X[1:-1] + X[:-2], axis=2) * 1000
    row = []
    for tok in (' L ', ' R '):
        sv = np.isin(dom, [j for j in jn if tok in j and (j.endswith('Clavicle') or j.endswith('UpperArm'))])
        o, l = sv & ~new, sv & new
        row.append(f'{tok.strip()}: installed rows n={o.sum()} p95 {np.percentile(A[:, o], 95, axis=1).max():.2f} max {A[:, o].max():.2f} | '
                   f'all rows p95 {np.percentile(A[:, sv], 95, axis=1).max():.2f} | lining rows n={l.sum()} max {A[:, l].max() if l.any() else 0:.2f}')
    print(f'{clip:15s}', ' || '.join(row), flush=True)
