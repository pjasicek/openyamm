"""Fit the existing articulated skull to the selected m628 body, preserving its hood."""
import bpy
import bmesh
import json
import sys
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common

bpy.ops.wm.open_mainfile(filepath=str(P / 'work/body_v2_parts.blend'))
parts = [o for o in bpy.data.objects if o.type == 'MESH']
old = bpy.data.objects['P02']
co = np.array([tuple(v.co) for v in old.data.vertices])
lo, hi = co.min(0), co.max(0)
for o in parts:
    pid = int(o.name[1:])
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [pid] * len(o.data.vertices))
    if pid >= 120 or o == old:
        bpy.data.objects.remove(o, do_unlink=True)
parts = [o for o in bpy.data.objects if o.type == 'MESH']

source = P / 'source/skull_parts.blend'
with bpy.data.libraries.load(str(source)) as (src, dst):
    names = tuple(n for n in src.objects if n.startswith('P') and n[1:].isdigit())
    dst.objects = list(names)
skull = dict(zip(names, dst.objects))
scale = float((hi[2] - lo[2]) / 1.578)
offset = Vector((float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2), float(lo[2])))
placement = Matrix.Translation(offset) @ Matrix.Scale(scale, 4)
mandible = skull['P01']
mc = np.array([tuple(v.co) for v in mandible.data.vertices])
condyles = mc[(np.abs(mc[:, 0]) > .28) & (mc[:, 2] > mc[:, 2].max() - .12) & (mc[:, 1] > -.1)]
assert len(condyles) > 0
pivot = condyles.mean(0); pivot[0] = 0
jaw = list(placement @ Vector(pivot))
for name, ob in skull.items():
    ob.name = 'Skull_' + name
    ob.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(ob)
    if name == 'P00':
        bm = bmesh.new(); bm.from_mesh(ob.data)
        stub = [v for v in bm.verts if v.co.z < .33 and abs(v.co.x) < .17 and -.07 < v.co.y < .34]
        bmesh.ops.delete(bm, geom=stub, context='VERTS')
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
        bm.to_mesh(ob.data); bm.free()
    pid = 2000 if name == 'P00' else 2001 if name == 'P01' else (
        2003 if np.mean([v.co.z for v in ob.data.vertices]) < .287 else 2002)
    ob.data.transform(placement @ ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    ob.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [pid] * len(ob.data.vertices))
    ob.vertex_groups.clear()
    for f in ob.data.polygons:
        f.use_smooth = True
    parts.append(ob)

mat = bpy.data.materials.new('SkeletonClay'); mat.diffuse_color = (.55, .52, .46, 1)
for ob in parts:
    ob.data.materials.clear(); ob.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT')
for ob in parts: ob.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
body = bpy.context.object; body.name = body.data.name = 'Body'
assert len(body.data.vertices) > 5000
bpy.context.scene['jaw_pivot'] = json.dumps(jaw)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/body_static.blend'))
(P / 'work/skull_fit.json').write_text(json.dumps({'scale': scale, 'offset': list(offset), 'jaw_pivot': jaw,
    'old_head_bounds': [lo.tolist(), hi.tolist()], 'reused_source': 'source/skull_parts.blend'}, indent=2))
scene = bpy.context.scene; common.workbench_clay(scene)
common.render_views(str(P / 'review/body_static'), .9, 1.95,
                    views=('front', 'left', 'back', 'three_quarter'), resolution=(600, 900))
common.render_views(str(P / 'review/skull_fit'), 1.68, .30,
                    views=('front', 'left', 'three_quarter'), resolution=(600, 600),
                    target=(float(offset.x), float(offset.y)))
