"""Even neck weights across the head graft (user review 2026-10-30: a line on the neck when the head turns). The head
carries Meshy's weights for a head and the body its own for a neck; at the seam they changed in a few millimetres,
so the look-at turn (B_Neck + B_Head, up to 60 deg) sheared the neck there. Every skin vertex within BAND of the cut
plane (work/graft.json z_cut) and within RADIUS of the neck axis (the neck, not the braid or the collar) takes
PASSES Jacobi passes of its edge neighbours' weights (all groups, renormalised), the outermost rings held fixed so
the smoothed band blends into the untouched weights above and below.
creature.json "neck_weights": {"band": m, "radius": m, "passes": n}. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NW = json.load(open(os.path.join(HERE, 'creature.json')))['neck_weights']
G = json.load(open(os.path.join(HERE, 'work', 'graft.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
zc = G['z_cut']; band, radius = NW['band'], NW['radius']
near = (np.abs(co[:, 2] - zc) < band * 1.6) & (gv == 0)
axis = co[near & (np.abs(co[:, 2] - zc) < 0.01)][:, :2].mean(0)
r = np.linalg.norm(co[:, :2] - axis, axis=1)
sel = (np.abs(co[:, 2] - zc) < band) & (r < radius) & (gv == 0)
names = [g.name for g in body.vertex_groups]
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
adj = [[] for _ in range(nv)]
for e in me.edges:
    i, j = e.vertices
    adj[i].append(j); adj[j].append(i)
idx = np.where(sel)[0]
inner = [i for i in idx if abs(co[i, 2] - zc) < band * 0.85]   # the outer rings stay as anchors
for _ in range(NW.get('passes', 12)):
    Wn = W.copy()
    for i in inner:
        if adj[i]:
            Wn[i] = 0.5 * W[i] + 0.5 * W[adj[i]].mean(0)
    W = Wn
for i in inner:                                       # four influences, renormalised (the runtime skin limit)
    keep = np.argsort(W[i])[-4:]; m = np.zeros_like(W[i]); m[keep] = W[i][keep]; W[i] = m
W[inner] /= np.maximum(W[inner].sum(1, keepdims=True), 1e-9)
for i in inner:
    for gi, w in enumerate(W[i]):
        if w > 1e-4:
            body.vertex_groups[gi].add([int(i)], float(w), 'REPLACE')
        elif any(e.group == gi for e in me.vertices[int(i)].groups):
            body.vertex_groups[gi].remove([int(i)])
print('NECKWEIGHTS smoothed', len(inner), 'verts within', band, 'm of z', round(zc, 3), 'radius', radius,
      'passes', NW.get('passes', 12))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
