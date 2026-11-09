"""Export a retopology variant (REA_TAG) with the Wyrm rig and all clips to review/viewer/mm6_wyrm_<tag>.glb."""
import os
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = os.environ['REA_TAG']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'retopo_{TAG}.blend'))
rig = bpy.data.objects['Wyrm_Rig']
mesh = bpy.data.objects[f'Wyrm_{TAG}']
rig.animation_data.action = bpy.data.actions['Standing']
bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig) or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.join(HERE, 'review', 'viewer'), exist_ok=True)
out = os.path.join(HERE, 'review', 'viewer', f'mm6_wyrm_{TAG}.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_image_format='AUTO', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
