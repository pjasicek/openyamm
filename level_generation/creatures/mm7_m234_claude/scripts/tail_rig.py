"""Tail bone chain for the gargoyle ('Tail' object from split_parts.py: the whip tail of P00 plus the spade P06).
Geodesic distance (Dijkstra on the tail's edges; the spade is linked to the nearest tail vertex) from the root ring (the
tail vertices within 1 cm of the body); centreline = centroids of 2 cm geodesic bands; N_BONES bones Tail_1..Tail_N at
equal arc length along it (parent B_Pelvis; Tail_N ends at the spade tip). Weights by the vertex's geodesic position:
linear blend between the two bones around it; the first ROOT_BLEND m blends from B_Pelvis. The object is parented to the
rig with an armature modifier. Writes work/tail_chain.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, heapq
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
N_BONES = int(os.environ.get('N_BONES', '8')); ROOT_BLEND = float(os.environ.get('ROOT_BLEND', '0.06'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; tail = bpy.data.objects['Tail']; body = bpy.data.objects['Body']; me = tail.data
co = np.array([tuple(tail.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
bc = np.array([tuple(body.data.attributes['orig_co'].data[i].vector) for i in range(len(body.data.vertices))])
kd = KDTree(len(bc))
for i, c in enumerate(bc):
    kd.insert(c, i)
kd.balance()
dist_body = np.array([kd.find(c)[2] for c in co])
adj = [[] for _ in range(nv)]
for e in me.edges:
    a, b = e.vertices; L = float(np.linalg.norm(co[a] - co[b])); adj[a].append((b, L)); adj[b].append((a, L))
# link separate pieces (the spade) to the nearest vertex of the main tube
pc = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pc)
main = pc == 0
for p in set(pc.tolist()) - {0}:
    ids = np.where(pc == p)[0]
    d = np.linalg.norm(co[ids][:, None] - co[main][None], axis=2) if len(ids) * main.sum() < 4e6 else None
    if d is None:
        continue
    i, j = np.unravel_index(np.argmin(d), d.shape); a, b = int(ids[i]), int(np.where(main)[0][j])
    adj[a].append((b, float(d[i, j]))); adj[b].append((a, float(d[i, j])))
g = np.full(nv, np.inf); h = []
for s_ in np.where(dist_body < 0.01)[0]:
    g[s_] = 0.0; heapq.heappush(h, (0.0, int(s_)))
while h:
    dd, a = heapq.heappop(h)
    if dd > g[a]:
        continue
    for b, L in adj[a]:
        if dd + L < g[b]:
            g[b] = dd + L; heapq.heappush(h, (dd + L, b))
Lmax = float(g[np.isfinite(g)].max())
cent = []
for k in range(int(Lmax / 0.02) + 1):
    m = (g >= k * 0.02) & (g < (k + 1) * 0.02)
    if m.any():
        cent.append(co[m].mean(0))
cent = np.array(cent)
seg = np.linalg.norm(np.diff(cent, axis=0), axis=1); arc = np.concatenate([[0], np.cumsum(seg)])
tipv = co[np.argmax(g)]
knots = [np.array([np.interp(t, arc, cent[:, k]) for k in range(3)]) for t in np.linspace(0, arc[-1], N_BONES + 1)]
knots[-1] = tipv
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; par = eb['B_Pelvis']
for i in range(N_BONES):
    b = eb.new(f'Tail_{i + 1}'); b.head = Vector(knots[i]); b.tail = Vector(knots[i + 1]); b.align_roll(Vector((0, 0, 1)))
    b.parent = par; b.use_connect = i > 0; par = b
bpy.ops.object.mode_set(mode='OBJECT')
tail.vertex_groups.clear()
G = {f'Tail_{i + 1}': tail.vertex_groups.new(name=f'Tail_{i + 1}') for i in range(N_BONES)}
G['B_Pelvis'] = tail.vertex_groups.new(name='B_Pelvis')
gl = np.where(np.isfinite(g), g, Lmax) / Lmax * N_BONES          # position in bone units along the chain
for vi in range(nv):
    x = min(gl[vi], N_BONES - 1e-6); i = int(x); f = x - i
    # blend centred on the joints: the vertex takes bone i, sharing with the next/previous near the joint
    w = {i: 1.0}
    if f > 0.5 and i + 1 < N_BONES:
        w = {i: 1.5 - f, i + 1: f - 0.5}
    elif f < 0.5 and i > 0:
        w = {i: 0.5 + f, i - 1: 0.5 - f}
    pel = float(np.clip(1 - g[vi] / ROOT_BLEND, 0, 1)) if np.isfinite(g[vi]) else 0.0
    for k, ww in w.items():
        G[f'Tail_{k + 1}'].add([vi], ww * (1 - pel), 'REPLACE')
    if pel > 0:
        G['B_Pelvis'].add([vi], pel, 'REPLACE')
tail.parent = rig
for md in [m for m in tail.modifiers if m.type == 'ARMATURE']:
    tail.modifiers.remove(md)
md = tail.modifiers.new('Armature', 'ARMATURE'); md.object = rig
json.dump({'knots': [k.tolist() for k in knots], 'length_m': float(arc[-1])}, open(os.path.join(HERE, 'work', 'tail_chain.json'), 'w'), indent=1)
print('TAILRIG bones', N_BONES, 'length m', round(float(arc[-1]), 3), 'root', np.round(knots[0], 3), 'tip', np.round(knots[-1], 3),
      'unreached verts', int((~np.isfinite(g)).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
