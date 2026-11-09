from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1]
for n in ['author_pilot','complete_motion','refine_clearance','head_carry','all_deformation']:
 s=P/'scripts'/(n+'.py');sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_full_uv.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/animated.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_full_uv.blend'))
s=P/'scripts/finish_master.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
