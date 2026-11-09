"""Head-only Meshy upload from work/head_uv.blend: the head faces (hpart > 0: face/neck/scalp, hair, hood) of the
candidate in rest pose, HeadUV as the only UV layer, one neutral material -> texturing/dru1_head_upload_r66.glb.
Usage: blender -b -P export_head_upload.py"""
import os, bpy, bmesh
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'head_uv.blend'))
rig = bpy.data.objects['Rig']; src = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')]
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
ob = src.copy(); ob.data = src.data.copy(); bpy.context.scene.collection.objects.link(ob)
ob.parent = None; ob.matrix_world = src.matrix_world.copy(); ob.hide_set(False); ob.hide_viewport = False
for m in list(ob.modifiers): ob.modifiers.remove(m)
ob.vertex_groups.clear()
bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['hpart']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
bm.to_mesh(ob.data); bm.free()
for l in [l.name for l in ob.data.uv_layers if l.name != 'HeadUV']: ob.data.uv_layers.remove(ob.data.uv_layers[l])
for at in [a.name for a in ob.data.attributes if a.name in ('hpart', 'uvpart', 'ReduceProtect')]: ob.data.attributes.remove(ob.data.attributes[at])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True; ob.data.materials.clear(); ob.data.materials.append(mat)
for o in bpy.data.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
out = os.path.join(HERE, 'texturing', 'dru1_head_upload_r66.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_animations=False,
                          export_skins=False, export_morph=False, export_attributes=False)
print('UPLOAD', out, len(ob.data.polygons), 'faces', [round(d, 3) for d in ob.dimensions])
