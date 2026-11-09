"""Joint-framed close-up specs from outside the body (run 2; closeups.py used one fixed direction per joint, which put the camera inside
the corpse or the floor in Death and Dead). Per clip and joint: the posed LOD0 surface; 98 directions round the joint (none below the
floor); the camera at D metres; the first mesh hit on the ray from the camera to the joint must be within REACH of the joint (nothing else
in front of it), the camera must be outside the mesh (an odd number of hits from it upward means inside) and above the floor. Among those,
the direction nearest the joint's preferred side wins. Prints name:clip:t:view:body:cam:target for vshots.sh. Args: [D]"""
import sys
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
D = float(sys.argv[1]) if len(sys.argv) > 1 else .6
REACH = .12
m = Model(Glb('review/viewer/liz_a.glb')); names = [n.get('name') for n in m.glb.json['nodes']]
OFF = np.cumsum([0] + [len(p['positions']) for p in m.primitives])
TR = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
J = {'kneeL': ('Bip01 L Calf', (.3, .3, 1)), 'kneeR': ('Bip01 R Calf', (-.3, .3, 1)), 'groin': ('Bip01 Pelvis', (0, -.2, 1)),
     'armL': ('Bip01 L UpperArm', (.7, -.4, .5)), 'armR': ('Bip01 R UpperArm', (-.7, -.4, .5)), 'elbowL': ('Bip01 L Forearm', (.4, .3, 1)),
     'neck': ('Bip01 Neck', (-.6, .2, .8)), 'mouth': ('Box01', (-.3, -.3, 1))}
g = np.pi * (3 - 5 ** .5); k = np.arange(98) + .5; zz = 1 - 2 * k / 98; rr = np.sqrt(1 - zz ** 2)
DIRS = np.c_[rr * np.cos(g * k), zz, rr * np.sin(g * k)]
def hits(o, d, A, E1, E2):
    h = np.cross(d, E2); det = (E1 * h).sum(1); s = o - A
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (s * h).sum(1) / det; q = np.cross(s, E1); v = (q @ d) / det; t = (E2 * q).sum(1) / det
    ok = (np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
    return np.sort(t[ok])
AX = [np.array(v, float) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
out = []
for c, t in (('Death', .7), ('Dead', .5), ('Hit2', .5), ('AttackMelee', .3), ('Death2', .6)):
    w = m.world(m.sample(c, float(t))); P = np.vstack([x[0] for x in m.skinned_positions(w)])
    A = P[TR[:, 0]]; E1 = P[TR[:, 1]] - A; E2 = P[TR[:, 2]] - A
    for key, (j, pref) in J.items():
        p = w[names.index(j)][:3, 3]; pref = np.array(pref, float); pref /= np.linalg.norm(pref); best = None
        for d in DIRS:
            cam = p + d * D
            if cam[1] < .06: continue
            hh = hits(cam, -d, A, E1, E2)
            if not len(hh) or hh[0] < D - (.2 if key == 'groin' else REACH): continue          # something in front of the joint, or nothing at all
            if sum(len(hits(cam, a_, A, E1, E2)) % 2 for a_ in AX) >= 2: continue      # camera inside the mesh (odd hits, majority of 6 axes: shells are open)
            if not all(len(hits(cam, a_, A, E1, E2)) == 0 or hits(cam, a_, A, E1, E2)[0] > .04 for a_ in AX): continue      # not pressed against a surface
            sc = d @ pref
            if best is None or sc > best[0]: best = (sc, cam)
        if best is None:
            for d in DIRS:                                         # fallback: the most open direction above the floor
                cam = p + d * D
                if cam[1] < .06: continue
                hh = hits(cam, -d, A, E1, E2); f = hh[0] if len(hh) else 0
                if best is None or f > best[0]: best = (f, cam)
            print('fallback', key, c, file=sys.stderr)
        cam = best[1]
        out.append(f"{key}_{c}:{c}:{t}:quarter:body:{cam[0]:.3f},{cam[1]:.3f},{cam[2]:.3f}:{p[0]:.3f},{p[1]:.3f},{p[2]:.3f}")
print(' '.join(out))
