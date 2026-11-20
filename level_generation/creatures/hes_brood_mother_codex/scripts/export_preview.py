"""Export an inspectable rigged GLB before texture handoff; no runtime installation."""
import bpy
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
pilot = 'pilot' in sys.argv
source = 'pilot_clips' if pilot else 'animated_master'
bpy.ops.wm.open_mainfile(filepath=str(P / f'work/{source}.blend'))
rig = bpy.data.objects['Rig']
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions['Standing']
if rig.animation_data.action.slots:
    rig.animation_data.action_slot = rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
for ob in bpy.context.scene.objects:
    ob.select_set(ob.type in ('ARMATURE', 'MESH'))
bpy.context.view_layer.objects.active = rig
out = P / f'work/{source}.glb'
bpy.ops.export_scene.gltf(filepath=str(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', out)
