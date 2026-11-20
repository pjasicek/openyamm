"""Head-only Meshy model -> objects Face (with neck), Eyes, Hair in metres, head-local (no placement). Teeth shell removed: MM9 has no jaw bone, the mouth stays closed.
The hair is a helmet-sized mushroom: shrunk onto the skull and neck by a soft cap on its shell thickness (front and crown stay, the bob narrows to MM9's slab), hidden skull under it removed.
Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.40
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
o.parent = None; o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices]) * S
for v, p in zip(me.vertices, P): v.co = Vector(p)
n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
order = np.argsort(-np.bincount(comp))
ids = {'Face': [order[0]], 'Hair': [order[1]], 'Eyes': [order[3], order[4]]}
print('COMPS', [int((comp == c).sum()) for c in order])
for k, cs in ids.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
Fc, Hr = bpy.data.objects['Face'], bpy.data.objects['Hair']
dg = bpy.context.evaluated_depsgraph_get()
bv = BVHTree.FromObject(Fc, dg)
H = np.array([v.co[:] for v in Hr.data.vertices]); m = len(H)
Q = np.zeros((m, 3)); Nn = np.zeros((m, 3)); D = np.zeros(m)
for i, p in enumerate(H):
    loc, nor, idx, dist = bv.find_nearest(Vector(p))
    Q[i] = loc; Nn[i] = nor; D[i] = dist
back = np.clip((H[:, 1] + 0.01) / 0.09, 0, 1); back = back * back * (3 - 2 * back)
dmax = 0.042 + 0.042 * back
Dn = dmax * np.tanh(D / dmax)
# the hairline lies on the skin: thickness grows from 2 mm at the rim, so tier A's bald forehead has no ledge
rim = (D < 0.007) & (H[:, 1] < 0.02)
dr = np.linalg.norm(H[:, None] - H[rim][None], axis=2).min(1)
front = np.clip((0.03 - H[:, 1]) / 0.05, 0, 1)
Dn = np.minimum(Dn, 0.002 + 0.45 * dr + 0.2 * (1 - front))
dsp = (Q - H) * (1 - Dn / np.maximum(D, 1e-6))[:, None]
hn = [[] for _ in range(m)]
for e in Hr.data.edges:
    a, b = e.vertices; hn[a].append(b); hn[b].append(a)
for _ in range(10):
    dsp = 0.5 * dsp + 0.5 * np.array([dsp[nb].mean(0) if nb else dsp[i] for i, nb in enumerate(hn)])
H2 = H + dsp
# MM9's slab: narrower than the skull's mushroom and shallower behind
x0 = 0.085; y0 = 0.06
ax = np.abs(H2[:, 0]); over = ax > x0
H2[over, 0] = np.sign(H2[over, 0]) * (x0 + (ax[over] - x0) * 0.55)
over = H2[:, 1] > y0
H2[over, 1] = y0 + (H2[over, 1] - y0) * 0.75
for v, p in zip(Hr.data.vertices, H2): v.co = Vector(p)
Hr.data.update()
dg.update()
print('HAIR before', np.round(H.min(0), 3), np.round(H.max(0), 3), 'after', np.round(H2.min(0), 3), np.round(H2.max(0), 3))
# Meshy left two pits and a ledge where the sculpt's hairline met the skull: relax the forehead just under the rim
bmf = bmesh.new(); bmf.from_mesh(Fc.data); bvh = BVHTree.FromObject(Hr, bpy.context.evaluated_depsgraph_get())
band = [v for v in bmf.verts if v.co.z > 0.045 and v.co.y < -0.03 and bvh.find_nearest(v.co, 0.02)[0] is not None]
for _ in range(8):
    mv = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in band}
    for v, c in mv.items(): v.co = v.co * 0.4 + c * 0.6
bmf.to_mesh(Fc.data); bmf.free(); Fc.data.update()
print('HAIR forehead band', len(band))
# skull faces hidden under the hair, and the hair's inner wall inside the skull
dg = bpy.context.evaluated_depsgraph_get()
bh = BVHTree.FromObject(Hr, dg)
bm = bmesh.new(); bm.from_mesh(Fc.data); bm.faces.ensure_lookup_table()
dead = set()
for f in bm.faces:
    c = f.calc_center_median(); hits = 0; tot = 0
    for dd in (f.normal, (f.normal + Vector((0.2, 0.1, 0.3))).normalized(), (f.normal + Vector((-0.2, 0.1, 0.3))).normalized(), (f.normal + Vector((0, 0.3, -0.1))).normalized()):
        loc, *_ = bh.ray_cast(c + dd * 1e-4, dd, 0.09); tot += 1; hits += loc is not None
    if hits == tot and c.z > -0.13: dead.add(f)
for _ in range(3):      # keep a margin under the hair's rim
    dead -= {f for f in dead if any(g not in dead for e in f.edges for g in e.link_faces)}
print('SKULL hidden faces', len(dead), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=list(dead), context='FACES')
bm.to_mesh(Fc.data); bm.free()
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    print('OBJ', ob.name, len(ob.data.vertices), len(ob.data.polygons), np.round(np.min([v.co[:] for v in ob.data.vertices], 0), 3), np.round(np.max([v.co[:] for v in ob.data.vertices], 0), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
