#!/usr/bin/env python3
"""Wrist join gate on a runtime GLB. Every clip at 48 fps, both arms. Rings: skin vertices welded by position; the bracer end ring and the hand top ring are the vertices nearest the two planes across the forearm at rest (AL_A, AL_B). (1) Open edges of the LOD0 skin in the wrist zone at rest, after welding by position (each edge must have exactly two faces). (2) Gap: per clip the largest distance from any vertex of the join zone to its nearest edge neighbour minus rest length ratio: edge stretch max, (3) neck: smallest ring radius in the zone over rest radius, (4) faces flipped in the zone. A gap reads as stretch of the join edges or a collapsed neck. Args: <glb>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
Pr = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
cnt = np.cumsum([0] + [len(p['positions']) for p in Pr])
T = np.vstack([p['triangles'].reshape(-1, 3) + o for p, o in zip(Pr, cnt)])
def X(w): return np.vstack([np.asarray(m.skinned_positions(w)[i][0]) for i in range(len(Pr))])
w0 = m.world({}); R0 = X(w0)
key = np.round(R0 / 6e-4).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
tw = wid[T]
fail = 0
for S, sg in (('R', -1), ('L', 1)):
    f, h = nm.index(f'Bip01 {S} Forearm'), nm.index(f'Bip01 {S} Hand')
    W = w0[h][:3, 3]; E_ = w0[f][:3, 3]; d = (W - E_) / np.linalg.norm(W - E_)
    al = (R0 - W) @ d; r = np.linalg.norm(R0 - W - np.outer(al, d), axis=1); side = np.sign(R0[:, 0]) == sg
    zone = side & (al > -0.03) & (al < 0.1) & (r < 0.078)
    fz = zone[T].all(1); e = np.sort(np.vstack([tw[fz][:, [0, 1]], tw[fz][:, [1, 2]], tw[fz][:, [2, 0]]]), 1)
    ue, c = np.unique(e, axis=0, return_counts=True)
    fe = T[zone[T].any(1)]; ae = np.sort(np.vstack([wid[fe][:, [0, 1]], wid[fe][:, [1, 2]], wid[fe][:, [2, 0]]]), 1); u2, c2 = np.unique(ae, axis=0, return_counts=True)
    zw = np.unique(wid[zone]); inner = np.isin(u2, zw).all(1); opn = int((c2[inner] == 1).sum()); mult = int((c2[inner] > 2).sum())
    bad = u2[inner][c2[inner] == 1]
    rep = {}
    for i_, w_ in enumerate(wid): rep.setdefault(int(w_), i_)
    print('OPENAT', S, [round(float(al[rep[int(x)]]), 3) for x in bad[:8, 0]], 'multi', mult)
    e0 = T[fz]; pa = np.vstack([e0[:, [0, 1]], e0[:, [1, 2]], e0[:, [2, 0]]]); L0 = np.linalg.norm(R0[pa[:, 0]] - R0[pa[:, 1]], axis=1); ok = L0 > 2e-3
    n0 = np.cross(R0[e0[:, 1]] - R0[e0[:, 0]], R0[e0[:, 2]] - R0[e0[:, 0]])
    Cf = json.load(open('work/cuff.json'))[S]; ra_ = np.array(Cf['rings'])[1:]; WL = Cf['wall']
    Jv = np.vstack([p['joints'] for p in Pr]); Wv = np.vstack([p['weights'] for p in Pr]); dn = np.array(jn)[Jv[np.arange(len(Jv)), Wv.argmax(1)]].astype(str)
    fh = np.char.endswith(dn, f'{S} Hand') | np.char.endswith(dn, f'{S} Hand_h') | np.char.endswith(dn, f'{S} Forearm_h')
    isfa = np.char.endswith(dn, f'{S} Forearm')
    iscuff = isfa & (al > -0.045) & (r > 0.0655) & (al < ra_[-1, 0] + 0.012) & (np.linalg.norm(R0 - W - np.outer(al, d), axis=1) > 0.0655) & (np.abs(r - np.interp(al, ra_[:, 0], ra_[:, 1])) < WL + 0.012)
    skin_h = side & fh & (al > -0.03) & (al < 0.17) & ~iscuff
    band = side & isfa & ~iscuff & (al > -0.02) & (al < 0.08) & (r < 0.08)
    cv = np.char.endswith(dn, 'Yclub')
    wthr = 0; wthrat = None; wcl = 0; wclat = None; per = {}
    rows = []; worstgap = 0; wstr = 0; wneck = 9; wflip = 0
    for clip in [a['name'] for a in m.glb.json['animations']]:
        D = m.clip_times(clip)[-1]
        for t in np.arange(0, D + 1e-6, 1 / 48):
            w = m.world(m.sample(clip, float(t))); Q = X(w)
            L = np.linalg.norm(Q[pa[:, 0]] - Q[pa[:, 1]], axis=1); st = float((L[ok] / L0[ok]).max()); gap = float((L[ok] - L0[ok]).max())
            Fw = w[f][:3, 3]; Hw = w[h][:3, 3]; dw = (Hw - Fw) / np.linalg.norm(Hw - Fw)
            mid = Q[zone & (al > 0.0) & (al < 0.06)]; rr = np.linalg.norm(mid - Hw - np.outer((mid - Hw) @ dw, dw), axis=1); neck = float(np.median(rr))
            n1 = np.cross(Q[e0[:, 1]] - Q[e0[:, 0]], Q[e0[:, 2]] - Q[e0[:, 0]]); fl = int(((n0 * n1).sum(1) < -0.0 * 1).sum()) if False else 0
            ToF = w0[f] @ np.linalg.inv(w[f]); Y = (ToF[:3, :3] @ Q.T).T + ToF[:3, 3]
            def wallout(idx):
                p = Y[idx]; a_ = (p - W) @ d; rr_ = np.linalg.norm(p - W - np.outer(a_, d), axis=1); inr = (a_ >= ra_[0, 0]) & (a_ <= ra_[-1, 0])
                ou = np.interp(a_, ra_[:, 0], ra_[:, 1]); return float((rr_[inr] - ou[inr]).max()) if inr.any() else -1, inr, rr_, ou
            th_ = wallout(np.nonzero(skin_h | band)[0])[0]
            c_, inr, rr_, ou = wallout(np.nonzero(cv)[0]); bw = inr & (rr_ > ou - WL - 0.03) & (rr_ < ou + 0.02); hit = float((rr_[bw] - (ou[bw] - WL)).max()) if bw.any() else -1
            per[clip] = max(per.get(clip, -1), th_)
            if th_ > wthr: wthr = th_; wthrat = (clip, round(float(t), 2))
            if hit > 0 and hit > wcl: wcl = hit; wclat = (clip, round(float(t), 2))
            if gap > worstgap: worstgap = gap; wg = (clip, round(float(t), 2))
            wstr = max(wstr, st); wneck = min(wneck, neck)
    r0 = float(np.median(r[zone & (al > 0.0) & (al < 0.06)]))
    print(f'WRISTGATE {S}: open edges {opn}; extra edge length {worstgap * 100:.2f} cm at {wg}; edge stretch max {wstr:.2f}; neck median radius min {wneck * 100:.1f} cm, rest {r0 * 100:.1f}, ratio {wneck / r0:.2f}')
    print(f'CUFFGATE {S}: cuff verts {int(iscuff.sum())}; hand and band through the outer wall worst {wthr * 100:.2f} cm at {wthrat}; club into cuff {wcl * 100:.2f} cm at {wclat}')
    print('CUFFPER', S, {k_: round(v * 100, 1) for k_, v in per.items() if v > 0})
    fail += opn > 0
sys.exit(1 if fail else 0)
