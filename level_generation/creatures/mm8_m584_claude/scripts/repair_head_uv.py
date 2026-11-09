"""Export the reviewed body and separate raven head for reference-guided texturing."""
import bpy, sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_final.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)   # natm: garment 0 skin, 9 eyes
head = np.array([int(pv[p.vertices[0]] in (2,20,21)) for p in me.polygons],np.int32)
assert 200 < head.sum() < len(me.polygons)/3
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', head.tolist())
print('HEAD faces', int(head.sum()), 'of', len(me.polygons))
# The replacement head upload is unwrapped after separation so only its surface is packed.
if 'HeadUV' not in me.uv_layers:me.uv_layers.new(name='HeadUV')

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
    for o in bpy.data.objects:o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.003, scale_to_bounds=True, correct_aspect=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    coords=np.array([tuple(x.uv) for x in ob.data.uv_layers.active.data])
    ob.data.calc_loop_triangles()
    area=sum(abs(np.cross(coords[t.loops[1]]-coords[t.loops[0]],coords[t.loops[2]]-coords[t.loops[0]]))/2 for t in ob.data.loop_triangles)
    assert area>.4 and np.min(coords.max(0)-coords.min(0))>.9,(area,coords.min(0),coords.max(0))
    print('HEAD_UV_AREA',float(area),flush=True)
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
export('head', os.path.join(HERE, 'texturing', 'raven_head_upload_v2.glb'), 'HeadUV')
