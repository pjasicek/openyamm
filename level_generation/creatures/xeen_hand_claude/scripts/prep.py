"""Import the Smart Topology return, scale the hand to HEIGHT (z extent, heel to the highest fingertip), centre x/y,
ground it (min z 0); forward -Y (the palm with the mouth faces -Y), up +Z (fingers), thumb +X (image right when the
palm faces the viewer, as the native frames). Reports connected pieces, boundary loops (centre, size) and enclosed
faces (no point of a face sees out along any of 162 directions). Saves work/clean_v1.blend (mesh 'Hand', face
attribute 'piece' and 'hidden') and close renders of the mouth (review/mouth_*.png)."""
import bpy, os, sys, bmesh, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 0.50
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
mn, mx = co.min(0), co.max(0)
k = HEIGHT / (mx[2] - mn[2])
off = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]))
for v in mesh.data.vertices:
    v.co = (v.co - off) * k
mesh.name = mesh.data.name = 'Hand'
mesh.data.materials.clear()
for p in mesh.data.polygons:
    p.use_smooth = True
me = mesh.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); n = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    stack = [v]; label[v.index] = n
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if label[o.index] < 0: label[o.index] = n; stack.append(o)
    n += 1
sizes = np.bincount(label); order = np.argsort(-sizes); remap = np.empty(n, int); remap[order] = np.arange(n)
label = remap[label]
co = np.array([tuple(v.co) for v in bm.verts])
for i in range(n):
    c = co[label == i]
    print(f'PIECE {i} verts {len(c)} min {np.round(c.min(0), 3).tolist()} max {np.round(c.max(0), 3).tolist()}')
# boundary loops
bedges = [e for e in bm.edges if e.is_boundary]
seen = set(); loops = []
for e in bedges:
    if e.index in seen: continue
    comp = []; stack = [e]; seen.add(e.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); stack.append(y)
    pts = np.array([tuple(v.co) for x in comp for v in x.verts])
    loops.append((len(comp), pts.mean(0), pts.max(0) - pts.min(0), int(label[comp[0].verts[0].index])))
for L in sorted(loops, key=lambda x: -x[0]):
    print(f'LOOP edges {L[0]} piece {L[3]} centre {np.round(L[1], 3).tolist()} size {np.round(L[2], 3).tolist()}')
# enclosed faces
bm.to_mesh(me)
bvh = BVHTree.FromObject(mesh, bpy.context.evaluated_depsgraph_get())
dirs = []
gold = math.pi * (3 - math.sqrt(5))
for i in range(162):
    z = 1 - 2 * (i + 0.5) / 162; r = math.sqrt(1 - z * z)
    dirs.append(Vector((r * math.cos(gold * i), r * math.sin(gold * i), z)))
hidden = np.zeros(len(me.polygons), bool)
for p in me.polygons:
    vs = [me.vertices[v].co for v in p.vertices]
    pts = [p.center] + [p.center.lerp(v, 0.75) for v in vs]
    seen_ = False
    for d in dirs:
        if d.dot(p.normal) <= 0.05: continue
        for q in pts:
            if bvh.ray_cast(q + p.normal * 2e-5 + d * 2e-5, d, 2.0)[0] is None:
                seen_ = True; break
        if seen_: break
    hidden[p.index] = not seen_
fpiece = np.array([label[p.vertices[0]] for p in me.polygons])
area = np.array([p.area for p in me.polygons])
print('HIDDEN faces', int(hidden.sum()), 'of', len(hidden), 'area share', round(float(area[hidden].sum() / area.sum()), 4),
      'per piece', {int(k): int((hidden & (fpiece == k)).sum()) for k in np.unique(fpiece)})
hc = np.array([tuple(p.center) for p in me.polygons])[hidden]
if len(hc):
    print('HIDDEN box', np.round(hc.min(0), 3).tolist(), np.round(hc.max(0), 3).tolist())
a = me.attributes.new('piece', 'INT', 'FACE'); a.data.foreach_set('value', fpiece.astype(np.int32))
a = me.attributes.new('hidden', 'INT', 'FACE'); a.data.foreach_set('value', hidden.astype(np.int32))
np.save(os.path.join(HERE, 'work', 'pieces.npy'), label)
co = np.array([tuple(v.co) for v in me.vertices])
print('SIZE', np.round(co.max(0) - co.min(0), 3).tolist(), 'factor', round(k, 4), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
fang = co[label > 0]
mc = (fang.min(0) + fang.max(0)) / 2 if len(fang) else co.mean(0)
print('FANG centre', np.round(mc, 3).tolist())
C.render(tuple(mc + np.array((0, -1, 0))), tuple(mc), 0.22, os.path.join(HERE, 'review', 'mouth_front.png'),
         res=(700, 500), floor=False)
C.render(tuple(mc + np.array((0.6, -0.6, 0.5))), tuple(mc), 0.22, os.path.join(HERE, 'review', 'mouth_quarter.png'),
         res=(700, 500), floor=False)
C.render(tuple(mc + np.array((0, -1, 0))), tuple(mc), 0.22, os.path.join(HERE, 'review', 'mouth_xray.png'),
         res=(700, 500), floor=False, bones=True)
