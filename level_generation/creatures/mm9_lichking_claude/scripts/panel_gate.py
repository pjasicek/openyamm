#!/usr/bin/env python3
"""Legs through a panel, per clip at 48 fps. In the Pelvis's bind frame, the panel's inner surface is sampled per height from its own skinned vertices (median depth of its row); a leg/boot/flap vertex inside the panel's
width and between its top and bottom is through when it lies past the panel's OUTER face (it would show on the outside). Prints per clip and panel: frames through / frames, worst depth in cm. Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
pr = [p for p in m.primitives]
nprim = int(sum(1 for mesh in m.glb.json['meshes'][:1] for _ in mesh['primitives']))
pr = pr[:nprim]
J = np.vstack([p['joints'] for p in pr]); W = np.vstack([p['weights'] for p in pr])
def share(pred):
    b = [i for i, n in enumerate(jn) if pred(n)]
    return (np.isin(J, b) * W).sum(1)
pf, pb = share(lambda n: n.startswith('XPanelF')), share(lambda n: n.startswith('XPanelB'))
leg = share(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe0')))
Vf, Vb, Vl = np.where(pf > 0.5)[0], np.where(pb > 0.5)[0], np.where(leg > 0.45)[0]
ip = names.index('Bip01 Pelvis'); Ibp = m.inverse_binds[jn.index('Bip01 Pelvis')]
def skin(w): return np.vstack([r[0] for r in m.skinned_positions(w)[:nprim]])
rest = skin(m.world({}))
print('verts F', len(Vf), 'B', len(Vb), 'leg', len(Vl))
res = {}
clips = [a['name'] for a in m.glb.json['animations'] if not want or a['name'] in want]
for c in clips:
    an = next(a for a in m.glb.json['animations'] if a['name'] == c)
    dur = max(m.glb.json['accessors'][s['input']]['max'][0] for s in an['samplers'])
    ts = np.arange(0, dur + 1e-6, 1 / 48)
    r = {}
    for nm, Vp, s in (('front', Vf, 1.0), ('back', Vb, -1.0)):
        bad = 0; worst = 0.0
        for t in ts:
            w = m.world(m.sample(c, float(t))); P = skin(w); Sp = w[ip] @ Ibp
            Q = (np.linalg.inv(Sp) @ np.c_[P, np.ones(len(P))].T).T[:, :3]
            q = Q[Vp]; ll = Q[Vl]
            # panel as a curve up -> outermost depth, in bins along its own length
            yb = np.linspace(q[:, 1].min(), q[:, 1].max(), 16)
            idx = np.digitize(q[:, 1], yb)
            yc, zc = [], []
            for b in range(1, len(yb)):
                sel = idx == b
                if sel.any(): yc.append(q[sel, 1].mean()); zc.append((q[sel, 2] * s).max())
            yc = np.array(yc); zc = np.array(zc)
            sel = (np.abs(ll[:, 0]) < np.abs(q[:, 0]).max()) & (ll[:, 1] < yc.max()) & (ll[:, 1] > yc.min())
            if not sel.any(): continue
            dep = ll[sel, 2] * s - np.interp(ll[sel, 1], yc, zc)
            d = dep.max()
            if d > 0.002: bad += 1; worst = max(worst, float(d))
        r[nm] = (bad, len(ts), round(worst * 100, 1))
    res[c] = r
    print(f'{c:16s} front {r["front"][0]}/{r["front"][1]} {r["front"][2]} cm   back {r["back"][0]}/{r["back"][1]} {r["back"][2]} cm', flush=True)
json.dump(res, open(out, 'w'), indent=0)
