"""Export Running's channels for replace_running_glb.py, without rebuilding geometry.
Blender arguments: -- [master.blend], default work/rig_v6.blend. Output: work/running_only.glb.
"""
import bpy
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(root / (args[0] if args else 'work/rig_v6.blend')))
rig = bpy.data.objects['Rig']
for action in list(bpy.data.actions):
    if action.name != 'Running':
        bpy.data.actions.remove(action)
rig.animation_data.action = bpy.data.actions['Running']
rig.animation_data.action_slot = rig.animation_data.action.slots[0]
# Preserve subframe stance keys through Blender's integer-frame sampling exporter.
act = rig.animation_data.action
substeps = act.get('export_substeps', 1)
for layer in act.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for key in curve.keyframe_points:
                    key.co.x *= substeps
                    key.handle_left.x *= substeps
                    key.handle_right.x *= substeps
act.frame_start *= substeps
act.frame_end *= substeps
bpy.context.scene.render.fps *= substeps
for obj in bpy.data.objects:
    obj.select_set(obj == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(root / 'work/running_only.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1,
                          export_skins=True, export_reset_pose_bones=True, export_anim_slide_to_zero=True)
