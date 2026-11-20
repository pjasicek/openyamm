"""Export neutral body and head texture uploads from the gated animated dwarf."""
import bpy, sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'motion_reduced.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
HEAD_PIECES = {1,2,3,6,9,10,13,19,20,24,25,30,33,34,35}
NECK_CUT = 1.075
print('HEAD neck cut z', round(NECK_CUT, 3), 'neck', round(rig.data.bones['B_Neck'].head_local.z, 3), 'head', round(rig.data.bones['B_Head'].head_local.z, 3))
head = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    vs = list(p.vertices)
    if (pv[vs[0]] == 0 and co[vs, 2].min() > NECK_CUT) or pv[vs[0]] in HEAD_PIECES:
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
    for at in [x.name for x in ob.data.attributes if x.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
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
export('body', os.path.join(HERE, 'texturing', 'm632_body_upload.glb'), 'UVMap' if 'UVMap' in me.uv_layers else me.uv_layers[0].name)
export('head', os.path.join(HERE, 'texturing', 'm632_head_upload.glb'), 'HeadUV')

# Preserve the locally modelled prop's material ownership through its independent retexture.
body=bpy.data.objects['Crossbow'];me=body.data
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
tri=body.modifiers.new('Triangulate','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=tri.name,index=0)
bpy.ops.object.modifier_apply(modifier=tri.name)
me=body.data;piece=me.attributes.get('piece') or me.attributes.new('piece','INT','POINT')
for face in me.polygons:
    for vi in face.vertices:piece.data[vi].value=face.material_index
me.attributes.new('head','INT','FACE')
export('prop',os.path.join(HERE,'texturing','m632_crossbow_upload.glb'),'UVMap')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work','master_uv.blend'))
