"""Export the editable round-4 scene; runtime packaging uses package_r4.py to preserve original motion bytes."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_figc_authoring.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['FighterChain']
for o in bpy.data.objects:o.select_set(o.type in {'MESH','ARMATURE'})
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_figc_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
