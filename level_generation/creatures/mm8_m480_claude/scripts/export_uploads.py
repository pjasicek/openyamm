"""Texture uploads from the gated, timed rig (work/rig_v5t.blend, rest pose, no armature):
- texturing/m480_body_upload.glb: the whole body mesh (sword not included) for a Meshy retexture with
  enable_original_uv: false; Meshy's own layout is copied back face by face afterwards (transfer_uv.py), because a
  Smart UV Project of this mesh would give Meshy hundreds of islands to paint inconsistently (flying demon lesson);
- head faces: skin (piece 0) faces whose vertices are mostly on B_Head/B_Neck and above the chin line, plus the
  goblin ear hoops and teeth; face attribute 'head' = 1, own UV layer 'HeadUV' filling 0..1 (Smart UV Project, 66 deg), exported alone as
  texturing/m480_head_upload.glb (enable_original_uv: true) for the head retexture.
Saves work/rig_v5h.blend (with 'head' and 'HeadUV'). Args: none"""
import bpy, sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'reduced.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
hg = {body.vertex_groups[n].index for n in ('B_Head', 'B_Neck')}
hw = np.array([sum(e.weight for e in v.groups if e.group in hg) for v in me.vertices])
co = np.array([tuple(v.co) for v in me.vertices])
chin = rig.data.bones['B_Head'].head_local.z - float(os.environ.get('CHIN_DROP', '0.08'))   # goblin: the whole jaw (0.02 cut the chin off)
# goblin: the four ear hoops and the teeth (pieces 60-78 at the mouth) go into the head set
CIRCLET = set(range(3,78))-{16,17,65}  # native lower tusks
head = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    vs = list(p.vertices)
    if (pv[vs[0]] == 0 and hw[vs].mean() > 0.6 and co[vs, 2].mean() > 1.31) or pv[vs[0]] in CIRCLET:
        head[p.index] = 1
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.tolist())
print('HEAD faces', int(head.sum()), 'of', len(me.polygons))
# head UV layer
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'texture_master.blend'))


def export(which, out, uv):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
    if which == 'head':
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != uv]:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    for at in [x.name for x in ob.data.attributes if x.name in ('piece', 'finger', 'head', 'orig_co')]:
        ob.data.attributes.remove(ob.data.attributes[at])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
    print('UPLOAD', which, out, len(ob.data.polygons), 'faces')
    bpy.data.objects.remove(ob, do_unlink=True)


os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
export('body', os.path.join(HERE, 'texturing', 'm480_body_upload.glb'), 'UVMap' if 'UVMap' in me.uv_layers else me.uv_layers[0].name)
export('head', os.path.join(HERE, 'texturing', 'm480_head_upload.glb'), 'HeadUV')
