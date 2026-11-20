"""Export the Reactor master (work/anim_v1.blend: all clips, Socket_Arc) to export/mm6_rea_lod0.glb.
fix_gltf.py then finalises materials (unlit glow, blended glass/flash) and STEP toggles."""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_blender as RB  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
RB.setup_materials(render=False)
rig = bpy.data.objects['Reactor_Rig']
rig.animation_data.action = bpy.data.actions['Standing']
bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o.name in ('Reactor', 'ReactorGlass', 'Reactor_Rig') or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm6_rea_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
