"""Shards and belly pockets on the UV-mapped goose (same topology and UVs; run after repose_v5.py).

Args: <in blend> <out blend> <report json>

1. Stray shards: reduced Meshy claws left needle tips (a vertex far from all its neighbours on a sliver, seen as a
   grey bar on the toes). A foot vertex whose offset from its neighbours' centroid exceeds SPIKE x the neighbours'
   own spread is moved onto that centroid; repeated until none is left.
2. Belly pockets: moving the legs 5 cm back onto MM9's joints pushed the belly skin into the Meshy ledge behind the
   legs, leaving hollows and a loose lip. A masked Laplacian relax (BELLY_IT iterations) evens the belly around the
   legs; the legs themselves, the wing rims and everything above BELLY_BOX stay.
"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
SPIKE = float(os.environ.get('SPIKE', '1.6'))
BELLY_IT = int(os.environ.get('BELLY_IT', '30'))
BELLY_BOX = (-0.075, 0.26, 0.20, 0.098)   # y0, y1, z1, |x| limit of the full relax (fades out over 0.03)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
n = len(bm.verts)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
P = np.array([tuple(v.co) for v in bm.verts])
nbr = [np.array([e.other_vert(v).index for e in v.link_edges]) for v in bm.verts]
rep = {}
feet = (piece == 0) & (P[:, 2] < 0.13)
moved = {}
sc = []
for i in np.nonzero(feet)[0]:
    nb = nbr[i]
    c = P[nb].mean(0); sc.append((float(np.linalg.norm(P[i] - c) / max(np.linalg.norm(P[nb] - c, axis=1).mean(), 1e-6)), float(np.linalg.norm(P[i] - c)), len(nb), np.round(P[i], 3).tolist()))
rep['top_scores'] = sorted(sc, reverse=True)[:8]
for it in range(8):
    k = 0
    for i in np.nonzero(feet)[0]:
        nb = nbr[i]
        if len(nb) < 3:
            continue
        c = P[nb].mean(0)
        spread = np.linalg.norm(P[nb] - c, axis=1).mean()
        off = np.linalg.norm(P[i] - c)
        if off > SPIKE * spread:
            moved.setdefault(int(i), np.round(P[i], 3).tolist())
            P[i] = c
            k += 1
    if k == 0:
        break
rep['spikes_moved'] = len(moved)
rep['spike_samples'] = list(moved.values())[:12]

# needle claws: chains of sliver triangles (long edge > 2 cm, altitude < 2.5 mm) form thin bars on the feet; each such
# cluster with a bar shape (length > 2 cm, width < 9 mm) is drawn in toward the foot end to NEEDLE of its length
NEEDLE = float(os.environ.get('NEEDLE', '0.1'))
me.calc_loop_triangles()
sl = []
for t in me.loop_triangles:
    a, b, c = P[list(t.vertices)]
    L = max(np.linalg.norm(a - b), np.linalg.norm(b - c), np.linalg.norm(c - a))
    h = np.linalg.norm(np.cross(b - a, c - a)) / max(L, 1e-9)
    if L > 0.02 and h < 0.0025 and min(a[2], b[2], c[2]) < 0.13:
        sl.append(list(t.vertices))
par = {}


def find(x):
    par.setdefault(x, x)
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x


for t in sl:
    for v in t[1:]:
        par[find(v)] = find(t[0])
groups = {}
for v in list(par):
    groups.setdefault(find(v), []).append(v)
rep['needles'] = []
for g_ in groups.values():
    X = P[g_]
    c = X.mean(0)
    u, s_, vt = np.linalg.svd(X - c)
    ext = (X - c) @ vt[0]
    length = ext.max() - ext.min()
    width = ((X - c) @ vt[1]).max() - ((X - c) @ vt[1]).min()
    if length < 0.02 or length > 0.06 or width > 0.009 or len(g_) < 5 or len(g_) > 40:
        rep.setdefault('bars_skipped', []).append([round(float(length), 3), round(float(width), 3), len(g_)])
        continue
    foot_c = P[(P[:, 2] < 0.04) & (np.sign(P[:, 0]) == np.sign(c[0]) if abs(c[0]) > 1e-3 else True)].mean(0)
    ax = vt[0] if (ext.max() * vt[0] + c - foot_c) @ vt[0] > 0 else -vt[0]
    e2 = (X - c) @ ax
    base = c + ax * e2.min()
    for v, q in zip(g_, e2 - e2.min()):
        P[v] = P[v] - ax * q * (1 - NEEDLE)
    rep['needles'].append({'at': np.round(c, 3).tolist(), 'length': round(float(length), 3), 'width': round(float(width), 3), 'verts': len(g_)})


def fade(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


y0, y1, z1, xl = BELLY_BOX
w = (fade(y0 - 0.03, y0, P[:, 1]) * (1 - fade(y1, y1 + 0.03, P[:, 1])) * (1 - fade(z1, z1 + 0.04, P[:, 2]))
     * (1 - fade(xl, xl + 0.03, np.abs(P[:, 0]))))
w[(piece != 0) | (chain >= 0) | (P[:, 2] < 0.075)] = 0
ids = np.nonzero(w > 1e-3)[0]
for _ in range(BELLY_IT):
    Q = P.copy()
    for i in ids:
        Q[i] = P[i] + 0.5 * w[i] * (P[nbr[i]].mean(0) - P[i])
    P = Q
rep['belly_verts'] = len(ids)
for v, p in zip(me.vertices, P):
    v.co = Vector(p)
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REPAIR ' + json.dumps(rep))
