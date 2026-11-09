#!/usr/bin/env python3
"""Legs through the coat and the tabard, per clip at 30 fps (thighs AND shins, every leg vertex). Cloth = vertices weighted over half to the
coat hinges (XCoat*) or the tabard links (XPanelF*); only the cloth's OUTER side counts (bind normal pointing away from the body axis; tabard:
forward). A leg vertex is through when its nearest outer-cloth vertex is within 4 cm and the leg vertex lies more than 3 mm beyond that cloth
vertex along the cloth's posed normal (it shows on the outside). Torso: the same with spine-weighted torso vertices against the coat's outer side
(a coat pushed into the back). Depth counts beyond the bind's own (a knee guard already through the coat side in the bind counts only as it moves further). Prints per clip: frames through / frames and the worst depth in cm, per cloth.
Args: <glb> <out json> [clips]"""
import json, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
pr = m.primitives; offs = np.cumsum([0] + [len(p['positions']) for p in pr])
J = np.vstack([p['joints'] for p in pr]); W = np.vstack([p['weights'] for p in pr])
T = np.vstack([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(m.skinned_positions(m.world({})), offs)])
def share(pred):
    b = [i for i, n in enumerate(jn) if pred(n)]; return (np.isin(J, b) * W).sum(1)
coat, tab = share(lambda n: n.startswith('XCoat')), share(lambda n: n.startswith('XPanelF'))
leg = share(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot')))
spine = share(lambda n: n in ('Bip01 Spine', 'Bip01 Spine1', 'Bip01 Pelvis'))
def skin(w): return np.vstack([r[0] for r in m.skinned_positions(w)])
def vnormals(P):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for c in range(3): np.add.at(N, T[:, c], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
P0 = skin(m.world({})); N0 = vnormals(P0)
rad = P0.copy(); rad[:, 1] = 0; rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
az = np.degrees(np.arctan2(P0[:, 0], -P0[:, 2]))                 # 0 at the back (glTF -z), as rig_bones.COAT
outer_coat = np.where((coat > 0.5) & ((N0 * rad).sum(1) > 0.2) & (P0[:, 1] < 0.86) & (np.abs(az) < 115))[0]       # below the belt band, not the open front edges
tx = np.abs(P0[:, 0]); outer_tab = np.where((tab > 0.5) & (N0[:, 2] * np.sign(np.median(P0[tab > 0.5, 2])) > 0.2) & (tx < 0.7 * tx[tab > 0.5].max()))[0]
legv = np.where((leg > 0.45) & (coat < 0.1) & (tab < 0.1))[0]; torso = np.where((spine > 0.6) & (coat < 0.1) & (tab < 0.1))[0]
print('outer coat', len(outer_coat), 'outer tabard', len(outer_tab), 'leg', len(legv), 'torso', len(torso))
def depths(P, N, cl, ob):
    d, i = cKDTree(P[cl]).query(P[ob]); dep = ((P[ob] - P[cl][i]) * N[cl][i]).sum(1); dep[d >= 0.06] = -1; return dep
BASE = {k: depths(P0, N0, cl, ob) for k, cl, ob in (('coat_leg', outer_coat, legv), ('tab_leg', outer_tab, legv), ('coat_torso', outer_coat, torso))}
print('bind already through (cm):', {k: round(float(v.max()) * 100, 1) for k, v in BASE.items()})
rep = {}
for clip in [a['name'] for a in doc['animations'] if not want or a['name'] in want]:
    Te = m.clip_times(clip)[-1]; fr = np.arange(0, Te + 1e-6, 1 / 30); res = {}
    acc = {k: [0, 0.0] for k in ('coat_leg', 'tab_leg', 'coat_torso')}
    for t in fr:
        P = skin(m.world(m.sample(clip, float(t)))); N = vnormals(P)
        for key, cl, ob in (('coat_leg', outer_coat, legv), ('tab_leg', outer_tab, legv), ('coat_torso', outer_coat, torso)):
            if not len(cl): continue
            dep = depths(P, N, cl, ob); ex = dep - np.maximum(BASE[key], 0)          # beyond what the bind already shows
            w = float(ex[dep > 0].max()) if (dep > 0).any() else 0.0
            if w > 0.003: acc[key][0] += 1; acc[key][1] = max(acc[key][1], float(w))
    rep[clip] = {k: dict(frames=v[0], of=len(fr), worst_cm=round(v[1] * 100, 1)) for k, v in acc.items()}
    print(f'{clip:15}', '  '.join(f'{k} {v[0]}/{len(fr)} {v[1]*100:.1f}cm' for k, v in acc.items()), flush=True)
json.dump(rep, open(out, 'w'), indent=1)
if len(sys.argv) > 4 and sys.argv[4] == 'debug':
    clip = want[0]; P = skin(m.world(m.sample(clip, 0.0))); N = vnormals(P)
    for key, cl, ob in (('coat_leg', outer_coat, legv), ('tab_leg', outer_tab, legv)):
        dep = depths(P, N, cl, ob) - np.maximum(BASE[key], 0); k = dep.argmax(); d, i = cKDTree(P[cl]).query(P[ob][k])
        print(key, 'worst', round(float(dep[k]) * 100, 1), 'leg vert bind', P0[ob][k].round(3), 'posed', P[ob][k].round(3), 'cloth vert bind', P0[cl][i].round(3), 'posed', P[cl][i].round(3), 'n', N[cl][i].round(2), 'dist', round(float(d), 3))
