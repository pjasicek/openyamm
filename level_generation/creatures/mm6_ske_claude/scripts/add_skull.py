"""Graft the skull-only Smart Topology model onto the body rig.

The skull parts blend (examine_parts.py, 1.578 high, faces -Y) holds the cranium with a neck stub (P00), the mandible
(P01) and separate teeth. The stub (|x| < 0.17, -0.07 < y < 0.34, z < 0.33) is cut and its opening filled; parts are
reduced (cranium/mandible by collapse, teeth to a few faces each). The skull is scaled to the old head's height
(mandible bottom 1.393 to crown 1.578) and placed with the stub axis over the atlas (P14), crown at 1.578. Cranium and
upper teeth go on Head, mandible and lower teeth on a new Jaw bone pivoting at the mandible condyles.
Piece ids: 2000 cranium, 2001 mandible, 2002 upper teeth, 2003 lower teeth.
Args: -- <skull parts blend> <rig blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector, Matrix
skull_blend, rig_blend, out = sys.argv[sys.argv.index('--') + 1:]
OLD_TOP, OLD_BOTTOM = 1.578, 1.393
STUB_C = np.array([0.0, 0.13])
TARGET = {'cranium': 2100, 'mandible': 420}

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(rig_blend))
rig = bpy.data.objects['Skeleton_Rig']; body = bpy.data.objects['Skeleton']
atlas = np.array(rig.matrix_world @ rig.data.bones['mixamorig:Head'].head_local)
with bpy.data.libraries.load(os.path.abspath(skull_blend)) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith('P')]
parts = [o for o in dst.objects if o is not None]
for o in parts:
    bpy.context.scene.collection.objects.link(o)
    o.data = o.data.copy()


def verts(o):
    return np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])


cran = next(o for o in parts if o.name == 'P00'); mand = next(o for o in parts if o.name == 'P01')
teeth = [o for o in parts if o not in (cran, mand)]

# cut the neck stub and close the opening
bm = bmesh.new(); bm.from_mesh(cran.data)
cut = [v for v in bm.verts if v.co.z < 0.33 and abs(v.co.x) < 0.17 and -0.07 < v.co.y < 0.34]
bmesh.ops.delete(bm, geom=cut, context='VERTS')
edges = [e for e in bm.edges if e.is_boundary]
bmesh.ops.holes_fill(bm, edges=edges, sides=0)
bm.to_mesh(cran.data); bm.free()

mt = verts(mand)
cond = mt[(np.abs(mt[:, 0]) > 0.28) & (mt[:, 2] > mt[:, 2].max() - 0.12) & (mt[:, 1] > -0.1)]
tmj = cond.mean(0) if len(cond) else np.array([0, 0.0, 0.62])
tmj[0] = 0.0
upper_z = 0.287                                 # between the upper (z 0.29-0.38) and lower (0.22-0.28) rows


def decimate(o, tris):
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if n > tris:
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = tris / n
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.ops.object.modifier_apply(modifier='dec')


decimate(cran, TARGET['cranium']); decimate(mand, TARGET['mandible'])
for t in teeth:
    decimate(t, 16)

s = (OLD_TOP - OLD_BOTTOM) / 1.578
off = Vector((atlas[0] - STUB_C[0] * s, atlas[1] - STUB_C[1] * s, OLD_TOP - 1.578 * s))
M = Matrix.Translation(off) @ Matrix.Scale(s, 4)
tmj_w = np.array(M @ Vector(tuple(tmj)))
groups = {}
for o in parts:
    o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if o is cran:
        bone, pid = 'Head', 2000
    elif o is mand:
        bone, pid = 'Jaw', 2001
    else:
        zc = verts(o)[:, 2].mean()
        lower = zc < M.translation.z + upper_z * s
        bone, pid = ('Jaw', 2003) if lower else ('Head', 2002)
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name='mixamorig:' + bone); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [pid] * len(o.data.vertices))
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials['Bone'])
    for p in o.data.polygons:
        p.use_smooth = True
    groups[pid] = groups.get(pid, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('mixamorig:Jaw')
eb.head = Vector(tuple(tmj_w)); eb.tail = Vector(tuple(tmj_w)) + Vector((0, -0.06, -0.03))
eb.parent = rig.data.edit_bones['mixamorig:Head']
eb.align_roll(Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')

for x in bpy.data.objects:
    x.select_set(x in parts or x == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('SKULL scale', round(s, 4), 'offset', [round(x, 3) for x in off], 'tmj', np.round(tmj_w, 3), 'tris by piece', groups)
print('TRIS total', sum(len(p.vertices) - 2 for p in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
