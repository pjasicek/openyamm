"""Replace the body's head pieces with the head-only Smart Topology model (work/head_v1_parts.blend from
examine_parts.py: P00 skull with mandible, P01 spiked helmet, the rest teeth and helmet rivets).
Old head pieces = every piece lying entirely above z 1.36 (skull P03, chin P15, teeth, eye blobs, helmet P07, rivets);
the spine column P11 stays (its top enters the skull). The new head is scaled uniformly to the old head's height
(lowest jaw point to spike tip) and centred on the old head's box in x/y. Reduced per piece (collapse): skull 2400,
helmet 760, each tooth 14, each rivet 10 triangles. New piece ids 100 skull, 101 helmet, 102.. teeth/rivets (the
weight rules put them all rigidly on B_Head). Args: -- <body blend> <head parts blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Matrix, Vector
body_blend, head_blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(body_blend))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
old = [p for p in set(pv.tolist()) if co[pv == p][:, 2].min() > 1.36 and p != 11]
om = np.isin(pv, old)
lo, hi = co[om].min(0), co[om].max(0)
print('HEAD old pieces', sorted(old), 'box', np.round(lo, 3).tolist(), np.round(hi, 3).tolist())
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(om)[0]], context='VERTS')
bm.to_mesh(me); bm.free()
with bpy.data.libraries.load(os.path.abspath(head_blend)) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith('P')]
parts = [o for o in dst.objects if o is not None]
for o in parts:
    bpy.context.scene.collection.objects.link(o); o.data = o.data.copy(); o.data.materials.clear()
hc = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in parts])
hlo, hhi = hc.min(0), hc.max(0)
s = (hi[2] - lo[2]) / (hhi[2] - hlo[2])
off = Vector(((lo[0] + hi[0]) / 2 - (hlo[0] + hhi[0]) / 2 * s, (lo[1] + hi[1]) / 2 - (hlo[1] + hhi[1]) / 2 * s, lo[2] - hlo[2] * s))
M = Matrix.Translation(off) @ Matrix.Scale(s, 4)
TARGET = {'P00': 2400, 'P01': 760}
tris = {}
for i, o in enumerate(sorted(parts, key=lambda o: o.name)):
    o.matrix_world = M @ o.matrix_world
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    t = TARGET.get(o.name, 14 if n > 120 else 10)
    if n > t:
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = t / n
        bpy.ops.object.modifier_apply(modifier='dec')
    pid = 100 + int(o.name[1:])
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [pid] * len(o.data.vertices))
    c = np.array([tuple(v.co) for v in o.data.vertices])
    o.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', c.ravel())
    for p in o.data.polygons:
        p.use_smooth = True
    tris[pid] = sum(len(p.vertices) - 2 for p in o.data.polygons)
for x in bpy.data.objects:
    x.select_set(x in parts or x == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
nc = np.array([tuple(v.co) for v in body.data.vertices])
print('HEAD scale', round(s, 4), 'new box', np.round(nc[nc[:, 2] > lo[2]].min(0), 3).tolist(), 'tris skull', tris[100], 'helmet', tris[101],
      'small pieces', sum(v for k, v in tris.items() if k > 101), 'body total', sum(len(p.vertices) - 2 for p in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
