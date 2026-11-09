"""Neck join relax (2026-10-30, after graft_head.py; positions and weights only, the UVs and both paints stay valid).

Args: <graft blend> <out blend> <report json> <graft report json> [radius m] [iterations] [taper m] [k0 mix]

The neck cut ring of graft_head.py lies where the body's front faces forward, so the loft left the body at a right
angle: a ledge all round the neck (a pale collar in the review viewer, where its downward face catches the light) and,
below it, the chest standing proud of the neck (a recess at the throat). Every vertex within RADIUS of the ring (body,
ring, loft and the head's neck stub; the skull is further than RADIUS) is relaxed with Taubin smoothing (lambda/mu, so the neck does
not shrink), falling off smoothly with the distance, so the breast flows into the neck. The weights there are
averaged over their neighbours the same way, so the relaxed surface also deforms smoothly.
"""
import bpy, bmesh, sys, json
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, GRAFT = a[:4]
RADIUS = float(a[4]) if len(a) > 4 else 0.05
ITERS = int(a[5]) if len(a) > 5 else 20
TAPER = float(a[6]) if len(a) > 6 else 0.05
K0_MIX = float(a[7]) if len(a) > 7 else 0.5     # ring radius target: (1 - K0_MIX) x body ring + K0_MIX x head ring
LAM, MU = 0.5, -0.53

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active
hl = bm.faces.layers.int['head']
kl = bm.verts.layers.int.get('kind')
n = len(bm.verts)
P = np.array([tuple(v.co) for v in bm.verts])
# the body ring: body vertices shared with head faces (the welded ring)
head_v = np.zeros(n, bool); body_v = np.zeros(n, bool)
for f in bm.faces:
    for v in f.verts:
        if f[hl] == 1:
            head_v[v.index] = True
        else:
            body_v[v.index] = True
ring = np.nonzero(head_v & body_v)[0]
RP = P[ring]
from mathutils.kdtree import KDTree
kd = KDTree(len(RP))
for i, p in enumerate(RP):
    kd.insert(p, i)
kd.balance()
d = np.array([kd.find(p)[2] for p in P])
kind = np.array([v[kl] for v in bm.verts]) if kl is not None else np.zeros(n, int)
# everything near the ring moves except the eyes (kind 2): body, ring, loft (4) and the head's neck stub
movable = (d < RADIUS) & (kind != 2)
w = np.clip(1 - d / RADIUS, 0, 1); w = w * w * (3 - 2 * w); w[~movable] = 0
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
# taper first: the body ring is the chest's cross-section (wider, and centred below the neck line); the body neck behind
# it narrows over TAPER towards the neck line (radius x K0 at the ring), and the loft between the ring and the head's
# neck ring follows, so there is no ledge to smooth away
G = json.load(open(GRAFT))
cb = RP.mean(0)
ch = np.array(G['placement']['head_ring_centre'])
ax = ch - cb; Lax = float(np.linalg.norm(ax)); ax /= Lax
chain = np.array([d_.value for d_ in me.attributes['chain'].data]) if 'chain' in me.attributes else np.full(n, -1)
rel = P - cb
t = rel @ ax / Lax
radial = rel - np.outer(rel @ ax, ax)
rr = np.linalg.norm(radial, axis=1)
rb = float(np.linalg.norm((RP - cb) - np.outer((RP - cb) @ ax, ax), axis=1).mean())
loft = kind == 4
hr = loft & (t > 0.9)
rh = float(rr[hr].mean()) if hr.any() else rb * 0.8
K0 = ((1 - K0_MIX) * rb + K0_MIX * rh) / rb
Tb = TAPER / Lax
sc = np.ones(n)
body_neck = body_v & ~head_v & (chain < 0) & (t < 0) & (t > -Tb) & (rr < 2.2 * rb)
u = np.clip((t + Tb) / Tb, 0, 1); u = u * u * (3 - 2 * u)
sc[body_neck] = 1 + (K0 - 1) * u[body_neck]
on_ring = np.zeros(n, bool); on_ring[ring] = True
sc[on_ring] = K0
tl = np.clip(t, 0, 1)
lf = loft & ~on_ring
sc[lf] = ((1 - tl[lf]) * K0 * rb + tl[lf] * rh) / ((1 - tl[lf]) * rb + tl[lf] * rh)
P = (cb + np.outer(rel @ ax, ax)) + radial * sc[:, None]
P0_taper = P.copy()
Q = P.copy()
for it in range(ITERS):
    for f_ in (LAM, MU):
        avg = np.array([Q[nb].mean(0) if nb else Q[i] for i, nb in enumerate(nbr)])
        Q = Q + (f_ * w)[:, None] * (avg - Q)
moved = np.linalg.norm(Q - np.array([tuple(v.co) for v in bm.verts]), axis=1)
for v in bm.verts:
    v.co = Q[v.index]
# weights: averaged over neighbours in the same falloff
Wd = [dict(v[dl].items()) for v in bm.verts]
for _ in range(4):
    new = []
    for i, nb in enumerate(nbr):
        if w[i] <= 0:
            new.append(Wd[i]); continue
        acc = {}
        for j in [i] + nb:
            for g, x in Wd[j].items():
                acc[g] = acc.get(g, 0) + x / (len(nb) + 1)
        mix = {g: Wd[i].get(g, 0) * (1 - w[i]) + acc.get(g, 0) * w[i] for g in set(acc) | set(Wd[i])}
        new.append(mix)
    Wd = new
for v in bm.verts:
    top = sorted(((g, x) for g, x in Wd[v.index].items() if x > 1e-4), key=lambda t: -t[1])[:4]
    s = sum(x for _, x in top)
    v[dl].clear()
    for g, x in top:
        if x / s >= 0.02:
            v[dl][g] = x / s
bm.to_mesh(me); bm.free()
rep = {'taper': {'ring_radius': rb, 'head_ring_radius': rh, 'K0': K0, 'body_verts': int(body_neck.sum()), 'length': TAPER},
       'ring_verts': int(len(ring)), 'relaxed_verts': int((w > 0).sum()), 'radius': RADIUS, 'iterations': ITERS,
       'max_move_mm': float(moved.max() * 1000), 'mean_move_mm': float(moved[w > 0].mean() * 1000)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('BLENDNECK ' + json.dumps(rep))
