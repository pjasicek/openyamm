"""work/spear_<tag>.blend -> work/spear_<tag>_anim.glb: the rig and its nine actions only, with the same exporter
settings as mm8_m568_claude/scripts/export_salamander.py (48 Hz sampling, reset pose bones, slide to zero).
Usage: blender -b -P export_anim.py -- <tag>"""
import bpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2]; tag = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=str(P / f'work/spear_{tag}.blend'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig; sc.render.fps = 48; rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str(P / f'work/spear_{tag}_anim.glb'), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1,
                          export_skins=True, export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_extras=False)
print('ANIM EXPORTED', tag)
