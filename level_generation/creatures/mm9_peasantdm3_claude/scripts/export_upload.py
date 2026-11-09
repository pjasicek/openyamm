"""Static upload GLB of the whole Body (rest pose) with one UV layer as TEXCOORD_0, no materials, no skin (as
texpass_uv.py's upload). Args: -- <blend> <out glb> <uv layer>"""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
dup = body.copy(); dup.data = body.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dup.vertex_groups.clear()
dm = dup.data
for name in [u.name for u in dm.uv_layers if u.name != argv[2]]:
    dm.uv_layers.remove(dm.uv_layers[name])
for name in [a.name for a in dm.attributes if not a.name.startswith('.') and a.name not in ('position',) and a.domain != 'CORNER']:
    try: dm.attributes.remove(dm.attributes[name])
    except Exception: pass
dm.materials.clear()
for o in bpy.data.objects: o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(argv[1]), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=argv[1], use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
print('UPLOAD', argv[1], len(dm.vertices), len(dm.polygons))
