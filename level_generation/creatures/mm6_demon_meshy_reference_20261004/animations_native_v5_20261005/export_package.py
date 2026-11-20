"""Export the isolated complete animated package, with standard portable presentation/effects."""
import bpy
import importlib.util
import json
from pathlib import Path

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage / 'authored_checkpoint.blend'))
scene = bpy.data.scenes['MM6_Demon_Native_Animations']
bpy.context.window.scene = scene
spec = importlib.util.spec_from_file_location('motion', stage / 'motion.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
death_weights = []
for frame in range(61):
    motion.activate('Death', frame)
    death_weights.append([k.value for k in scene.objects['Demon_Death_Plume'].data.shape_keys.key_blocks][1:])
motion.activate('Walk_Native', 0)
# The NLA exporter samples singular visibility transforms; restore the authored object transforms afterward.
object_matrices = {obj: obj.matrix_basis.copy() for obj in scene.objects}
for obj in scene.objects:
    if obj.type != 'CAMERA':
        obj.hide_set(False)
    obj.select_set(obj.type != 'CAMERA')
    for owner in [obj, obj.data.shape_keys if obj.type == 'MESH' else None]:
        if owner is not None and owner.animation_data:
            owner.animation_data.action = None
            for track in owner.animation_data.nla_tracks:
                track.mute = True
bpy.context.view_layer.objects.active = scene.objects['Demon_Native_Rig']
bpy.ops.export_scene.gltf(
    filepath=str(stage / 'mm6_demon_native_animations.glb'), export_format='GLB',
    use_selection=True, use_active_scene=True, export_animations=True, export_animation_mode='NLA_TRACKS',
    export_frame_range=False, export_force_sampling=True, export_frame_step=1, export_all_influences=True,
    export_def_bones=False, export_optimize_animation_size=False, export_materials='EXPORT',
    export_normals=True, export_yup=True, export_cameras=False, export_lights=False,
    export_morph=True, export_morph_animation=True)
spec = importlib.util.spec_from_file_location('normalize_export', stage / 'normalize_export.py')
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
normalizer.normalize(stage / 'mm6_demon_native_animations.glb', death_weights)
for obj, matrix in object_matrices.items():
    obj.matrix_basis = matrix
motion.activate('Walk_Native', 0)
scene.objects['Demon_Native_Rig'].hide_set(True)
for obj in scene.objects:
    obj.select_set(False)
scene.objects['Demon_Native_Mesh'].select_set(True)
bpy.context.view_layer.objects.active = scene.objects['Demon_Native_Mesh']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'MATERIAL'
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
text = bpy.data.texts.new('SELECT_ANIMATION.py')
text.write('''# Change CLIP and Run Script in Blender's Text Editor. Space plays the selected clip.
CLIP = "Walk_Native"
# Available: Standing, Walk_Native, Hit, Fidget, Death, Ash_Remains, Attack, Walking, Running
import bpy
scene = bpy.context.scene
ends = {"Standing":6,"Walk_Native":54,"Hit":36,"Fidget":30,"Death":60,"Ash_Remains":6,
        "Attack":36,"Walking":50,"Running":32}
assert CLIP in ends
for obj in scene.objects:
    for owner in [obj, obj.data.shape_keys if obj.type == 'MESH' else None]:
        if owner is None or owner.animation_data is None:
            continue
        owner.animation_data.action = None
        for track in owner.animation_data.nla_tracks:
            track.mute = track.name != CLIP
scene.render.fps = 48
scene.frame_start, scene.frame_end = 0, ends[CLIP]
scene.frame_set(0)
''')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_native_animations.blend'), compress=True)
print('Exported complete GLB and ordinary editable Blender project.', flush=True)
