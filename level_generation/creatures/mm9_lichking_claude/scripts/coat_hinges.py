"""Coat hinge points per sector (rig_bones.COAT) at the belt and knee heights: the outermost coat point along the sector's azimuth ray
(Blender frame, 0 deg = back +y, +90 = +x). Written into rig.json['coat']. Args: <asm npz> <rig json>"""
import sys, json, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section
from rig_bones import COAT, COAT_Z
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
t = tri[comp[tri[:, 0]] == names.index('torso')]
R = json.load(open(sys.argv[2])); out = {}
for k, a in COAT.items():
    d = np.array([np.sin(np.radians(a)), np.cos(np.radians(a))]); pts = []
    for z in COAT_Z:
        L = section(co, t, np.array([0, 0, z]), np.array([0, 0, 1.0]))
        P = np.vstack([l['pts'] for l in L])[:, :2]
        r = P @ d; perp = np.abs(P @ np.array([-d[1], d[0]]))
        ok = (r > 0) & (perp < 0.03)
        if not ok.any(): ok = r > 0
        rr = r[ok].max() - 0.01
        pts.append([float(d[0] * rr), float(d[1] * rr), float(z)])
    out[k] = pts; print(k, np.round(pts, 3).tolist())
R['coat'] = out; json.dump(R, open(sys.argv[2], 'w'), indent=0)
