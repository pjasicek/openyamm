#!/usr/bin/env python3
"""Body faces the hands touch (a60's arm/hand gate: Taunt L 0 -> 3.1 cm, ResurrectSpell L 0 -> 3.4, Death2 L 0.1 -> 2.1 when
the chest, trousers and tatter under the hands were cut): every installed LOD0 face that is not a hand face and whose posed
centroid comes within R m of a posed hand vertex in any sampled frame (every clip, HZ) is kept exactly; mirrored in x at rest.
Usage: hand_contact.py <sets tag> <out name>  -> work/<out name>.npy (per GLB face)   (env R default 0.05, HZ default 15, CLIPS optional list)"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.05')); HZ = float(os.environ.get('HZ', '15'))
tag, outn = sys.argv[1:3]
m = Model(Glb(str(HERE / 'before' / 'mm9_zombie.glb')))
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
Ts = [np.asarray(p['triangles']).reshape(-1, 3) for p in m.primitives[:3]]
offs = np.cumsum([0] + [len(t) for t in Ts])
hand_f = s['cls'][:len(Ts[0])] == CLS.index('hands')
hand_v = np.unique(Ts[0][hand_f])
target = ~np.isin(s['cls'], [CLS.index(c) for c in ('hands', 'lining')])
hit = np.zeros(len(s['cls']), bool)
CL = [c for c in os.environ.get('CLIPS', '').split(',') if c]
for clip in [a['name'] for a in m.glb.json['animations'] if not CL or a['name'] in CL]:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        sk = m.skinned_positions(m.world(m.sample(clip, float(t))))
        tree = cKDTree(np.asarray(sk[0][0])[hand_v])
        for k in range(3):
            P = np.asarray(sk[k][0]); c = P[Ts[k]].mean(1)
            d, _ = tree.query(c, distance_upper_bound=R)
            hit[offs[k]:offs[k + 1]] |= d < R
hit &= target
# mirror at rest (the two sides cut differently otherwise)
rest = [np.asarray(p) for p, _ in m.skinned_positions(m.world({}))[:3]]
cen = np.concatenate([P[T].mean(1) for P, T in zip(rest, Ts)])
mir = cen[hit] * [-1, 1, 1]
hit |= target & (cKDTree(mir).query(cen)[0] < 0.006)
print('HANDCONTACT', int(hit.sum()), {CLS[c]: int((hit & (s['cls'] == c)).sum()) for c in np.unique(s['cls'][hit])})
np.save(HERE / 'work' / f'{outn}.npy', hit)
