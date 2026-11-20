#!/usr/bin/env python3
"""Legs through the coat and the tabard (thighs AND shins), per clip at 30 fps, by rays (r9: counted only where the ray meets the cloth's outer side). For each leg vertex, a ray towards the body's axis
(coat: across the spine's axis, from the vertex to the axis; tabard: backwards along the spine frame's forward): if it meets the cloth
within 8 cm, the cloth lies between the leg and the body there, so the leg is outside it: through, by the distance to the hit. Legs in front of
the open coat meet nothing. Cloth = triangles whose three vertices are weighted over half to XCoat* (coat) or XPanelF* (tabard). Torso: the
same with spine-weighted vertices against the coat. Bind overlaps are subtracted per vertex. Args: <glb> <out json> [clips]"""
import json, sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else None
m = Model(Glb(glb)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
pr = m.primitives; offs = np.cumsum([0] + [len(p['positions']) for p in pr])
J = np.vstack([p['joints'] for p in pr]); W = np.vstack([p['weights'] for p in pr])
T = np.vstack([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(m.skinned_positions(m.world({})), offs)])
def share(pred):
    b = [i for i, n in enumerate(jn) if pred(n)]; return (np.isin(J, b) * W).sum(1)
coat, tab = share(lambda n: n.startswith('XCoat')), share(lambda n: n.startswith('XPanelF'))
leg = share(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot')))
spine = share(lambda n: n in ('Bip01 Spine', 'Bip01 Spine1', 'Bip01 Pelvis'))
Tc = T[(coat[T] > 0.5).all(1)]; Tt = T[(tab[T] > 0.5).all(1)]
# r9: only the cloth's OUTER surface counts (the coat and the tabard are thin closed shells: a leg under a lifted flap meets the inner
# surface first, from its own side). Outer = bind face normal away from the body axis (coat) or forward (tabard).
_P0 = np.vstack([np.asarray(p['positions'], float) for p in pr])
def _fn(Tr): n_ = np.cross(_P0[Tr[:, 1]] - _P0[Tr[:, 0]], _P0[Tr[:, 2]] - _P0[Tr[:, 0]]); return n_ / np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
_c = _P0[Tc].mean(1); _rad = _c * [1, 0, 1]; _rad /= np.maximum(np.linalg.norm(_rad, axis=1, keepdims=True), 1e-9)
Tc = Tc[(_fn(Tc) * _rad).sum(1) > 0]
Tt = Tt[_fn(Tt)[:, 2] * np.sign(np.median(_P0[Tt][:, :, 2])) > 0]
P00 = np.vstack([np.asarray(p['positions'], float) for p in pr])
legv = np.where((leg > 0.45) & (coat < 0.1) & (tab < 0.1) & (P00[:, 1] < 0.88))[0][::2]          # not the trouser top under the belt (inside the torso)
torso = np.where((spine > 0.6) & (coat < 0.1) & (tab < 0.1))[0]
isp = names.index('Bip01 Spine'); ipl = names.index('Bip01 Pelvis')
def skin(w): return np.vstack([r[0] for r in m.skinned_positions(w)])
def hits(O, D, P, Tr, maxd=0.08):
    """distance along D from each origin to the first cloth triangle (inf if none within maxd)"""
    A, B, C = P[Tr[:, 0]], P[Tr[:, 1]], P[Tr[:, 2]]; e1, e2 = B - A, C - A; out = np.full(len(O), np.inf)
    for s in range(0, len(O), 256):
        o, d = O[s:s + 256, None], D[s:s + 256, None]
        h = np.cross(d, e2[None]); det = (e1[None] * h).sum(-1); inv = 1 / np.where(np.abs(det) < 1e-12, 1e-12, det)
        sv = o - A[None]; u = (sv * h).sum(-1) * inv; q = np.cross(sv, e1[None]); v = (d * q).sum(-1) * inv; t = (e2[None] * q).sum(-1) * inv
        ok = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < maxd) & (np.abs(det) > 1e-12)
        tt = np.where(ok, t, np.inf); k = tt.argmin(1); first = tt[np.arange(len(k)), k]
        # r9: through only when the first cloth face met is met on its OUTER side (the ray runs against its normal): the leg is outside
        # the cloth. A leg under a lifted flap meets the flap's inner side first and is not through.
        nrm = np.cross(e1, e2)[k]; facing = (nrm * D[s:s + 256]).sum(1) < 0
        out[s:s + 256] = np.where(facing, first, np.inf)
    return out
def dirs(w, P, idx, kind):
    Rs = w[isp][:3, :3]; up = Rs[:, 0] / np.linalg.norm(Rs[:, 0])          # Bip01 Spine's x axis runs up the spine (Biped)
    if kind == 'tab':
        f = -np.cross(up, Rs[:, 1] / np.linalg.norm(Rs[:, 1])); c = P[idx] * 0 + f
        # forward = the side the tabard hangs on: pick by the tabard's centre
        tc = P[np.unique(Tt)].mean(0) - w[ipl][:3, 3]; f = f if f @ tc > 0 else -f
        return np.repeat(-f[None], len(idx), 0)
    o = w[ipl][:3, 3]; d = P[idx] - o; d -= np.outer(d @ up, up); return -d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
def measure(w):
    P = skin(w); r = {}
    for key, Tr, ob, kind in (('coat_leg', Tc, legv, 'coat'), ('tab_leg', Tt, legv, 'tab'), ('coat_torso', Tc, torso, 'coat')):
        r[key] = hits(P[ob], dirs(w, P, ob, kind), P, Tr)
    return r
B0 = measure(m.world({}))
print('cloth tris coat', len(Tc), 'tabard', len(Tt), 'legs', len(legv), 'bind through', {k: int(np.isfinite(v).sum()) for k, v in B0.items()})
rep = {}
for clip in [a['name'] for a in doc['animations'] if not want or a['name'] in want]:
    Te = m.clip_times(clip)[-1]; fr = np.arange(0, Te + 1e-6, 1 / 30); acc = {k: [0, 0.0, 0] for k in B0}
    for t in fr:
        r = measure(m.world(m.sample(clip, float(t))))
        for k, v in r.items():
            bad = np.isfinite(v) & ~np.isfinite(B0[k])
            if bad.any(): acc[k][0] += 1; acc[k][1] = max(acc[k][1], float(v[bad].max())); acc[k][2] = max(acc[k][2], int(bad.sum()))
    rep[clip] = {k: dict(frames=v[0], of=len(fr), worst_cm=round(v[1] * 100, 1), max_verts=v[2]) for k, v in acc.items()}
    print(f'{clip:15}', '  '.join(f'{k} {v[0]}/{len(fr)} {v[1]*100:.1f}cm n{v[2]}' for k, v in acc.items()), flush=True)
json.dump(rep, open(out, 'w'), indent=1)
if len(sys.argv) > 4 and sys.argv[4] == 'debug':
    clip, t = sys.argv[5], float(sys.argv[6]); w = m.world(m.sample(clip, t)); r = measure(w)
    for k in ('coat_leg', 'tab_leg'):
        bad = np.isfinite(r[k]) & ~np.isfinite(B0[k]); idx = legv[bad]
        print(k, 'through verts', bad.sum(), 'bind positions (glTF):'); P0 = skin(m.world({}))
        for i in idx[:12]: print('   ', P0[i].round(3), 'hit at', round(float(r[k][legv == i][0]) * 100, 1), 'cm', 'bones', [jn[j] for j, ww in zip(J[i], W[i]) if ww > 0.2])
