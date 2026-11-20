"""Export work/anim.blend (rig, clips, materials) as export/hes_custodian_lod0.glb (LOD0 with every clip; Standing is
the scene's action), as hes_turrets_claude/scripts/build_actor_v2.py's export. Args: none."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc  # noqa: E402
bpy.ops.wm.open_mainfile(filepath=cc.path('work/anim.blend'))
rig = bpy.data.objects['Custodian_Rig']; body = bpy.data.objects['Custodian']
if 'part' in body.data.attributes:
    body.data.attributes.remove(body.data.attributes['part'])
standing = bpy.data.actions['Standing']
rig.animation_data.action = standing
if len(standing.slots):
    rig.animation_data.action_slot = standing.slots[0]
for o in bpy.context.scene.objects:
    o.select_set(o in (rig, body))
bpy.context.view_layer.objects.active = rig
os.makedirs(cc.path('export'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=cc.path('export/hes_custodian_lod0.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
                          export_force_sampling=True, export_frame_step=1, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False,
                          export_image_format='AUTO', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', [a.name for a in bpy.data.actions])
