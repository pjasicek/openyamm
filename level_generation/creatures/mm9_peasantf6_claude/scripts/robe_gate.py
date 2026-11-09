#!/usr/bin/env python3
"""Nothing through the robe, per clip. Legs (shins, boots): a vertex outside the robe's outer surface whose closest robe point lies above the hem band has gone through the cloth (a boot below or beyond the hem has its closest point on the hem band and is fine). Hands are arm_hand_gate.py's.
Cords: a cord vertex more than 1 cm behind the outer surface is under the cloth. Signed distance to the closest triangle of the posed outer robe. 48 fps on Walking and Running, 24 elsewhere. Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); prims = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
sk = [i for i, n in enumerate(jn) if (n[:1] == 'x' and not n.startswith('xpony')) or n == 'XCOM_skirt']; leg = [i for i, n in enumerate(jn) if 'Calf' in n or 'Foot' in n or 'Toe' in n]; cord = [i for i, n in enumerate(jn) if n.startswith('Y')]
sw = (np.isin(J, sk) * W).sum(1); lw = (np.isin(J, leg) * W).sum(1); cw = (np.isin(J, cord) * W).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in prims]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(prims, offs)])
n_p = len(prims)
def allpos(w): return np.concatenate([r[0] for r in m.skinned_positions(w)][:n_p])
R0 = allpos(m.world({})); c0 = R0[tri].mean(1); n0 = np.cross(R0[tri[:, 1]] - R0[tri[:, 0]], R0[tri[:, 2]] - R0[tri[:, 0]])
axis = np.array([0, 0, 0.0]); rad = c0.copy(); rad[:, 1] = 0
rob = (sw[tri] > 0.3).all(1) & ((n0 * rad).sum(1) > 0)                 # outer faces of the chains
hem_y = R0[np.unique(tri[rob])][:, 1].min()
# bind height above the hem of each face
fh = c0[:, 1] - hem_y
F = np.where(rob)[0]; legv = np.where(lw > 0.5)[0]; cordv = np.where((cw > 0.5) & (R0[:, 1] < 0.99))[0]
print('robe faces', len(F), 'leg verts', len(legv), 'cord verts', len(cordv), 'hem y', hem_y)
def signed(P, Q):
    tr = P[tri[F]]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    # the mirrored GLB flips nothing in signs of (p - q) . n as windings were kept outward
    _, ids = cKDTree(c).query(Q, k=6); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q)); ff = np.zeros(len(Q), int)
    for k in range(6):
        i = ids[:, k]; q, _b = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1); ff[u] = i[u]
    return sd, ff, best
sgn = 1.0
s_, _, _ = signed(R0, R0[F[0:0]] if False else c0[F[:50]] - (n0[F[:50]] / np.maximum(np.linalg.norm(n0[F[:50]], axis=1, keepdims=True), 1e-12)) * 0.01)
if np.median(s_) > 0: sgn = -1.0                                        # windings point inward
print('sign', sgn)
res = {}
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; fps = 48 if clip in ('Walking', 'Running', 'Backpedal', 'BackpedalRun') else 24; T = np.arange(0, dur + 1e-6, 1 / fps)
    f1 = f2 = 0; d1 = d2 = 0.0; wh = None
    for t in T:
        P = allpos(m.world(m.sample(clip, float(t))))
        sd, ff, dist = signed(P, P[legv]); sd = sd * sgn
        bad = (sd > 0.003) & (fh[F[ff]] > 0.14) & (dist < 0.08)
        if bad.any(): f1 += 1; d1 = max(d1, float(sd[bad].max()))
        sd, ff, dist = signed(P, P[cordv]); sd = sd * sgn
        bad = (sd < -0.012) & (dist < 0.08)
        if bad.any():
            f2 += 1; d2 = max(d2, float(-sd[bad].min())); i_ = np.argmin(sd); wh = (round(float(R0[cordv[i_], 1]), 3), round(float(t), 2))
    res[clip] = dict(frames=f1, of=len(T), max_cm=round(d1 * 100, 1), cord_frames=f2, cord_cm=round(d2 * 100, 1))
    print(f'{clip:14} legs through robe {f1:3}/{len(T)} {d1 * 100:.1f} cm   cords under robe {f2:3}/{len(T)} {d2 * 100:.1f} cm  bind height, time {wh}', flush=True)
json.dump(res, open(out, 'w'), indent=1)
