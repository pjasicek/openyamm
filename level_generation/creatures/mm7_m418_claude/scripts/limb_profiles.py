"""Limb centrelines of the m418 troglodyte skin (piece 0) from geodesic rings: for each tip (claw of each hand, front
toe of each foot, tail tip, front of the hood) the geodesic distance over the skin's edge graph is cut into 2 cm bands;
each band's centroid and mean radius give the profile (the limb's centreline until the bands merge into the body).
Meshy's auto-rig joints were unusable on this body (a hand on the tail, the knees asymmetric), so the joints are fitted
from these profiles (fit_joints.py). Writes work/limb_profiles.json. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
import heapq
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Body'].data
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])
E = E[(pv[E[:, 0]] == 0) & (pv[E[:, 1]] == 0)]
w = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
ADJ = [[] for _ in range(len(co))]
for (a, b), l in zip(E.tolist(), w.tolist()):
    ADJ[a].append((b, l)); ADJ[b].append((a, l))


def dijkstra(t):                                         # Blender's Python has no scipy
    d = np.full(len(co), np.inf); d[t] = 0.0; h = [(0.0, t)]
    while h:
        dv, v = heapq.heappop(h)
        if dv > d[v]:
            continue
        for u, l in ADJ[v]:
            if dv + l < d[u]:
                d[u] = dv + l; heapq.heappush(h, (d[u], u))
    return d
skin = np.where(pv == 0)[0]


def pick(mask, key):
    idx = skin[mask[skin]]
    return int(idx[np.argmin(key(co[idx]))])


x, y, z = co[:, 0], co[:, 1], co[:, 2]
TIPS = {
    'R_hand': pick((x < -0.3) & (y < -1.0) & (z > 0.3), lambda c: c[:, 2]),
    'L_hand': pick((x > 0.3) & (y < -1.0) & (z > 0.3), lambda c: c[:, 2]),
    'R_foot': pick((x < -0.1) & (z < 0.08), lambda c: c[:, 1]),
    'L_foot': pick((x > 0.1) & (z < 0.08), lambda c: c[:, 1]),
    'tail': pick(np.ones(len(co), bool), lambda c: -c[:, 1]),
    'hood': pick(np.ones(len(co), bool), lambda c: c[:, 1]),
}
out = {}
BAND = 0.02
for name, t in TIPS.items():
    d = dijkstra(t)
    prof = []
    for k in range(0, 80):
        m = (d >= k * BAND) & (d < (k + 1) * BAND)
        if m.sum() < 3:
            continue
        c = co[m].mean(0); r = float(np.linalg.norm(co[m] - c, axis=1).mean())
        prof.append({'d': round(k * BAND, 3), 'c': [round(float(v), 4) for v in c], 'r': round(r, 4), 'n': int(m.sum())})
    out[name] = {'tip': co[t].round(4).tolist(), 'profile': prof}
    print('PROFILE', name, 'tip', co[t].round(3).tolist())
    for p in prof[::2]:
        print('   d %.2f c %s r %.3f n %d' % (p['d'], np.round(p['c'], 3).tolist(), p['r'], p['n']))
json.dump(out, open(os.path.join(HERE, 'work', 'limb_profiles.json'), 'w'), indent=0)
