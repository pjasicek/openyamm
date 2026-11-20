"""work/uv.blend (or the given blend) -> work/geom_export.glb: Body skinned geometry only (8 influences, normalised;
no clips, no images), node named KnightPlate, materials KnightPlate_A (slot 0, body) and KnightHelm_A (slot 1,
helmet), for swap_multi.py. Usage: blender -b -P export_geom.py [-- <blend>]"""
import os, sys, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]) if args else os.path.join(HERE, 'work', 'uv.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for slot, name in zip(body.material_slots, ('KnightPlate_A', 'KnightHelm_A')):
    other = bpy.data.materials.get(name)
    if other is not None and other is not slot.material:
        other.name = name + '_unused'
    slot.material.name = name
body.name = 'KnightPlate'
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_limit_total(limit=8); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'geom_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=True,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in body.data.polygons), [s.material.name for s in body.material_slots])
