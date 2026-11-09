"""Body-only texture upload v2 (user approval 2026-10-20: retexture the FINAL mesh to remove the speckles the UV
carry-over left on the reworked coat). Opens work/rig_v6.blend (final mesh, rest pose, 'head' face attribute and the
carried HeadUV kept as they are) and exports the whole body mesh, without armature, to
texturing/m422_body_upload_v2.glb for a Meshy retexture with enable_original_uv: false (Meshy's own layout is copied
back face by face with transfer_uv.py). Args: none"""
import bpy, sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()


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
export('body', os.path.join(HERE, 'texturing', 'm422_body_upload_v2.glb'), 'UVMap')
