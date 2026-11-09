"""Body retexture prep for the 70 % djinn (user 2026-10-14: "body might need retexture": blotchy bracer, dark slashes
on the skin). Candidate Cand_70 of work/ladder_neck_protect.blend (head set and upper neck kept). The runtime atlas is
2080x1024: body texels in u < 1024/2080, head set in u > 1056/2080. Body faces (UV centroid u < 0.5) get fresh Smart UV
islands, concave-packed into the unit square, used as body = upload UV x (1024/2080, 1); head faces keep their UVs.
Upload: the body square at 92 %, the head set (its atlas half rescaled) in a 0.08 corner so Meshy sees the whole
djinn. Out: work/uv_master.blend (object Body + Rig, runtime UVs), work/body_upload.glb, work/uv_tris.npy."""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY_W, HEAD_U0 = 1024 / 2080, 1056 / 2080
UP_BODY, UP_HEAD = .92, .08
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_neck_protect.blend'))
o = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_70')]; rig = bpy.data.objects['Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = o.vertex_groups.get('ReduceProtect')
if g:
    o.vertex_groups.remove(g)
me = o.data; uv = me.uv_layers.active.data
is_body = np.array([sum(uv[l].uv[0] for l in p.loop_indices) / len(p.loop_indices) < .5 for p in me.polygons])
head_uv = {l: tuple(uv[l].uv) for p in me.polygons if not is_body[p.index] for l in p.loop_indices}
# fresh body islands on a body-only copy (packing in place would move the head islands)
tmp = o.copy(); tmp.data = me.copy(); tmp.parent = None; tmp.modifiers.clear(); bpy.context.collection.objects.link(tmp)
bm = bmesh.new(); bm.from_mesh(tmp.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not is_body[f.index]], context='FACES'); bm.to_mesh(tmp.data); bm.free()
bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(float(os.environ.get('UV_ANGLE', '66'))), island_margin=.003, area_weight=0, correct_aspect=True, scale_to_bounds=True)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=.003, margin_method='FRACTION', shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
tuv = tmp.data.uv_layers.active.data
body_faces = [p for p in me.polygons if is_body[p.index]]
assert len(body_faces) == len(tmp.data.polygons)
square = {}
for p, q in zip(body_faces, tmp.data.polygons):
    for l, m in zip(p.loop_indices, q.loop_indices):
        square[l] = tuple(tuv[m].uv)
bpy.data.objects.remove(tmp, do_unlink=True)
# runtime UVs: body square -> left 1024 px of the atlas
for l, (u, v) in square.items():
    uv[l].uv = (u * BODY_W, v)
for x in list(bpy.data.objects):                       # the source Body and the other candidates go first
    if x.type == 'MESH' and x is not o:
        bpy.data.objects.remove(x, do_unlink=True)
o.name = 'Body'; o.hide_render = False
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
# upload: body square at 92 %, head half rescaled into a 0.08 corner
dup = o.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
bpy.context.collection.objects.link(dup); duv = dup.data.uv_layers.active.data; tris = []
for p in dup.data.polygons:
    for l in p.loop_indices:
        if l in square:
            u, v = square[l]; duv[l].uv = (u * UP_BODY, v * UP_BODY)
        else:
            u, v = head_uv[l]; duv[l].uv = (UP_BODY + (u - HEAD_U0) / (1 - HEAD_U0) * UP_HEAD, v * UP_HEAD)
dup.data.materials.clear(); m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
dup.data.calc_loop_triangles()
for t in dup.data.loop_triangles:
    tris.append([0 if is_body[t.polygon_index] else 1] + [c for l in t.loops for c in duv[l].uv])
np.save(os.path.join(HERE, 'work', 'uv_tris.npy'), np.array(tris, np.float32))
bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'body_upload.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_attributes=False, export_morph=False)
print('UV body faces', int(is_body.sum()), 'head faces', int((~is_body).sum()))
