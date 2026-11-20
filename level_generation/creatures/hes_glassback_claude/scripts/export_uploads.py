"""Texture uploads from the rig (rest pose, no armature), after hes_guard_claude/scripts/export_uploads.py:
- texturing/hgb_body_upload.glb: the whole mesh for a Meshy retexture with enable_original_uv: false (Meshy's own
  layout is copied back face by face by transfer_uv.py);
- head faces (face attribute 'head'): centroid in front of the neck cut (y < NECK_Y) and above the front feet; own
  UV layer 'HeadUV' filling 0..1 (Smart UV Project 66 deg), exported alone as texturing/hgb_head_upload.glb.
work/rig_v1.blend -> work/rig_v1h.blend"""
import bpy, os, sys, math
import bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
NECK_Y = -1.04
bpy.ops.wm.open_mainfile(filepath=C.path('work/rig_v1.blend'))
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]; me = body.data
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
co = np.array([tuple(v.co) for v in me.vertices])
head = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    c = co[list(p.vertices)].mean(0)
    head[p.index] = int(c[1] < NECK_Y and c[2] > 0.42)
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.tolist())
print('HEAD faces', int(head.sum()), 'of', len(me.polygons))
if not me.uv_layers:
    me.uv_layers.new(name='UVMap')
me.uv_layers[0].name = 'UVMap'
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(head[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=C.path('work/rig_v1h.blend'))


def export(which, out, uv):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
    if which == 'head':
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != uv]:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    if 'head' in ob.data.attributes:
        ob.data.attributes.remove(ob.data.attributes['head'])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
    print('UPLOAD', which, os.path.basename(out), len(ob.data.polygons), 'faces')
    bpy.data.objects.remove(ob, do_unlink=True)


os.makedirs(C.path('texturing'), exist_ok=True)
export('body', C.path('texturing/hgb_body_upload.glb'), 'UVMap')
export('head', C.path('texturing/hgb_head_upload.glb'), 'HeadUV')
