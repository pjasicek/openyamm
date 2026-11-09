import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh']
for o in bpy.data.objects:o.select_set(o in [r,b,ax])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(P/'work/round1_motion.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
runpy.run_path(str(P/'scripts/trace_final.py'),run_name='__main__',init_globals={'INPUT':'work/round1_motion.glb'})
