"""Body texture upload for a peasant with a grafted head (graft_head_parts.py), from the gated rig (work/rig_v5.blend,
rest pose): the grafted head keeps its own Meshy texture and UV layer 'HeadUV', so only the body goes to Meshy.
- face attribute 'head' (1 on the grafted head's faces, from weld_neck.py) selects the head;
- texturing/<prefix>_body_upload.glb: every non-head face, UV 'UVMap', neutral material, for a retexture with
  enable_original_uv: false (Meshy's layout is copied back face by face by transfer_uv.py).
Saves work/rig_v5h.blend (with 'head'). Args: none"""
import bpy, bmesh, sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(HERE, 'creature.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
head = np.zeros(len(me.polygons), np.int32)          # written by weld_neck.py before the seam was welded
me.attributes['head'].data.foreach_get('value', head)
if 'UVMap' not in me.uv_layers:
    me.uv_layers.new(name='UVMap')
me.uv_layers.active = me.uv_layers['UVMap']
print('HEAD faces', int(head.sum()), 'of', len(me.polygons), 'HeadUV' in me.uv_layers)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5h.blend'))

ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
ob.parent = None; ob.matrix_world = body.matrix_world.copy()
for m in list(ob.modifiers):
    ob.modifiers.remove(m)
ob.vertex_groups.clear()
bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 1], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(ob.data); bm.free()
for l in [l.name for l in ob.data.uv_layers if l.name != 'UVMap']:
    ob.data.uv_layers.remove(ob.data.uv_layers[l])
for at in [x.name for x in ob.data.attributes if x.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    ob.data.attributes.remove(ob.data.attributes[at])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
ob.data.materials.clear(); ob.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
out = os.path.join(HERE, 'texturing', f"{C['prefix']}_body_upload.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
print('UPLOAD body', out, len(ob.data.polygons), 'faces')
