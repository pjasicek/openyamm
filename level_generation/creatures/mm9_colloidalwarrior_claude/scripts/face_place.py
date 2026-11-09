"""The closed head shell (head_fix.py) placed in figure space as face_npz.py does, without the voxel wrap (its 2.5 mm closure frayed
the creases between the throat rolls): normals recalculated, symmetric decimation to TARGET triangles. Args: <in blend> <out blend> [target]"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; TARGET = int(a[2]) if len(a) > 2 else 30000
S, OY, OZ, BACK = [float(os.environ.get(k, d)) for k, d in (('S', 0.8), ('OY', 0.04), ('OZ', 0.654), ('BACK', 0.75))]
bpy.ops.wm.open_mainfile(filepath=IN)
f = bpy.data.objects['Face']; me = f.data
for v in [v for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Eyes' for v in o.data.vertices] + list(me.vertices):
    c = np.array(v.co[:]); c[1] = c[1] * BACK if c[1] > 0 else c[1]
    v.co = Vector(c * S + np.array([0, OY, OZ]))
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
bpy.context.view_layer.objects.active = f
for o in bpy.data.objects: o.select_set(o is f)
n0 = len(me.polygons)
if n0 > TARGET:
    m = f.modifiers.new('D', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET / n0; m.use_symmetry = True; m.symmetry_axis = 'X'
    bpy.ops.object.modifier_apply(modifier=m.name)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for r in range(6):      # folded slivers (fan fills, Meshy shards): a vertex whose faces disagree goes to its neighbours' average
    bm.normal_update(); bad = []
    for v in bm.verts:
        if not v.link_edges or not v.link_faces: continue
        c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        if min(g.normal.dot(v.normal) for g in v.link_faces) < 0.2: bad.append((v, c))
    for v, c in bad: v.co = c
    print('DESPIKE', r, len(bad))
print('PLACED tris', len(bm.faces), 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
