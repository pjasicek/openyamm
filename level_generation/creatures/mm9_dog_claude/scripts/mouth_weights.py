"""Jaw ownership of the reduced dog (MM9 weights a few chin vertices to Xjawpiv; our jaw is the whole mandible).

Args: <in blend> <out blend> <report json>
- In front of the mouth corners (y < YC) the skin is two parts (mouth_carve.py): the lower one is rigid on Xjawpiv, the
  upper one keeps its rig weights without any jaw share.
- Behind the corners: floor of the mouth pocket fades out towards the hinge (points behind the pivot would rise into the
  palate), the cheek and the skin under the jaw fade over a soft band so nothing tears at the corners; the neck stays.
- Teeth: each piece rigid on its own jaw (by the lip plane), seated 4.5 mm towards its gum, because the slit took that
  much off the lips. Eyes share the socket's weights. A tongue piece rests on the floor of the pocket, rigid on the jaw.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
YC = -0.41
UP, JAW, SKULL = 'Xmouth', 'Xjawpiv', 'Xhead'
f = lambda y: 0.7475 + 0.03 * (y + 0.5)
ss = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
arm = bpy.data.objects['MM9_Rig']
me = body.data
# tongue first, so it is one more piece below
bm = bmesh.new(); bm.from_mesh(me)
pl, cl = bm.verts.layers.int['piece'], bm.verts.layers.int['chain']
r = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
for v in r['verts']:
    x, y, z = v.co
    # a flattened tongue: blunt tip forward, widest behind it, the root sinks into the pocket floor
    t = (y + 1) / 2
    w = 0.022 * (0.72 + 0.28 * np.sin(min(t * 1.6, 1.0) * np.pi / 2))
    v.co = Vector((x * w, -0.432 + y * 0.053, 0.7385 + z * 0.0075 - 0.004 * t))
    v[pl] = 2; v[cl] = -1
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
for g in (UP, JAW, SKULL):
    if g not in body.vertex_groups:
        body.vertex_groups.new(name=g)
names = [g.name for g in body.vertex_groups]
gi = {n: i for i, n in enumerate(names)}
co = np.array([tuple(v.co) for v in me.vertices])
n = len(co)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
piece = np.array([d.value for d in me.attributes['piece'].data])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
body_v = piece == 0
t_b = tris[body_v[tris].all(1)]
E = np.unique(np.sort(np.r_[t_b[:, [0, 1]], t_b[:, [1, 2]], t_b[:, [2, 0]]], 1), axis=0)
mask = body_v & (co[:, 1] < YC) & (co[:, 2] > 0.62)
par = np.arange(n)


def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x


for a, b in E[mask[E[:, 0]] & mask[E[:, 1]]]:
    ra, rb = find(a), find(b)
    if ra != rb:
        par[ra] = rb
idx = np.nonzero(mask)[0]
roots = np.array([find(i) for i in idx])
u, c = np.unique(roots, return_counts=True)
assert len(u) == 2, ('expected upper and lower jaw', c)
z0 = co[idx[roots == u[0]], 2].mean(); z1 = co[idx[roots == u[1]], 2].mean()
low_root = u[0] if z0 < z1 else u[1]
lower = np.zeros(n, bool); lower[idx[roots == low_root]] = True
upper = mask & ~lower
d = f(co[:, 1]) - co[:, 2]
y, z = co[:, 1], co[:, 2]
inner = body_v & (np.abs(co[:, 0]) < 0.09) & (z > 0.705) & (z < 0.80) & (y < -0.355) & (y >= YC)
outer = body_v & ~mask & ~inner
w = np.zeros(n)
w[lower] = 1
w[inner] = (ss(-0.004, 0.006, d) * (1 - ss(-0.405, -0.372, y)))[inner]
w[outer] = (ss(-0.003, 0.016, d) * (1 - ss(-0.395, -0.315, y)) * (1 - ss(0.065, 0.12, d)))[outer]
# soften around the corners only
deg = np.maximum(np.bincount(E.ravel(), minlength=n), 1).astype(float)
hold = ~(body_v & (y > -0.43)) | inner
for _ in range(6):
    acc = np.zeros(n)
    np.add.at(acc, E[:, 0], w[E[:, 1]]); np.add.at(acc, E[:, 1], w[E[:, 0]])
    nw = 0.5 * w + 0.5 * acc / deg
    nw[hold] = w[hold]
    w = nw
Wu = W.copy()
Wu[:, gi[JAW]] = 0
s = Wu.sum(1)
Wu[s <= 1e-6, gi[SKULL]] = 1
Wu /= Wu.sum(1, keepdims=True)
Wn = W.copy()
Wn[body_v] = (Wu * (1 - w)[:, None])[body_v]
Wn[body_v, gi[JAW]] += w[body_v]
# pieces
tp = tris[(~body_v)[tris].all(1)]
par2 = np.arange(n)


def find2(x):
    while par2[x] != x:
        par2[x] = par2[par2[x]]; x = par2[x]
    return x


for a, b, c_ in tp:
    for p_, q_ in ((a, b), (b, c_)):
        ra, rb = find2(p_), find2(q_)
        if ra != rb:
            par2[ra] = rb
ids = np.nonzero(~body_v)[0]
rr = np.array([find2(i) for i in ids])
teeth = {'upper': 0, 'lower': 0}
P = co.copy()
body_ids = np.nonzero(body_v)[0]
for r_ in np.unique(rr):
    v = ids[rr == r_]
    cn = co[v].mean(0)
    if cn[2] < 0.6:
        continue
    if cn[2] > 0.8:     # eye: the socket's weights
        dd = ((co[body_ids] - cn) ** 2).sum(1)
        near = body_ids[np.argsort(dd)[:12]]
        m = Wn[near].mean(0)
        Wn[v] = 0
        Wn[v] = m
        continue
    tongue = np.ptp(co[v, 1]) > 0.09
    side = 'lower' if (tongue or cn[2] < f(cn[1]) - 0.0028) else 'upper'
    Wn[v] = 0
    Wn[v, gi[JAW if side == 'lower' else UP]] = 1
    if not tongue:
        P[v, 2] += 0.0045 if side == 'upper' else -0.0045
        teeth[side] += 1
for i, v in enumerate(me.vertices):
    v.co = Vector(tuple(P[i]))
# four influences, normalised
order = np.argsort(-Wn, 1)[:, :4]
out = np.zeros_like(Wn)
rows = np.arange(n)[:, None]
out[rows, order] = Wn[rows, order]
out[out < 0.015] = 0
out /= out.sum(1, keepdims=True)
for j, name in enumerate(names):
    g = body.vertex_groups[name]
    g.remove(list(range(n)))
    ii = np.nonzero(out[:, j])[0]
    for i in ii:
        g.add([int(i)], float(out[i, j]), 'REPLACE')
rep = {'lower': int(lower.sum()), 'upper': int(upper.sum()), 'inner': int(inner.sum()), 'teeth': teeth,
       'tris': len(tris), 'jaw_verts': int((out[:, gi[JAW]] > 0.5).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('MOUTH ' + json.dumps(rep))
