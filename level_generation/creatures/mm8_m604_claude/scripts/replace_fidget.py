from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1];s=p/'scripts/retarget.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend'),str(p/'work/fidget_source.blend'),str(p.parents[2]/'anim_library/humanoid_set/Armed.glb')+':ArmedIdleAlert1:Fidget'];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/texture_master.blend'));bpy.data.actions.remove(bpy.data.actions['Fidget'])
with bpy.data.libraries.load(str(p/'work/fidget_source.blend'),link=False) as (src,dst):dst.actions=['Fidget']
dst.actions[0].use_fake_user=True;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/texture_master.blend'))
