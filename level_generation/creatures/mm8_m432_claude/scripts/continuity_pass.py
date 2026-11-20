import os,sys,runpy,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['FINISH_INPUT']='work/rig_gripped.blend'
runpy.run_path(str(P/'scripts/finish_motion.py'),run_name='__main__')
# Keep the already-cleared death, feet and other clips; this pass replaces only attack and cast arm paths.
with bpy.data.libraries.load(str(P/'work/rig_before_continuity.blend'),link=False) as (src,dst):
 dst.actions=[n for n in src.actions if n not in ('Attack','Cast')]
for ac in dst.actions:
 name=ac.name.rsplit('.',1)[0] if ac.name.rsplit('.',1)[-1].isdigit() else ac.name
 old=bpy.data.actions.get(name)
 if old is not ac:bpy.data.actions.remove(old)
 ac.name=name;ac.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_raw_continuity.blend'))
os.environ['ARM_INPUT']='work/rig_raw_continuity.blend';os.environ['ARM_OUTPUT']='work/rig_smooth_arms.blend';os.environ['ARM_CLIPS']='Attack,Cast';os.environ['ARM_PHI']='170';os.environ.pop('ARM_SIDES',None)
runpy.run_path(str(P/'scripts/smooth_arm_fit.py'),run_name='__main__')
os.environ['BAKE_ONLY']='1';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_smooth_arms.blend'),str(P/'work/rig_final_motion.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/assemble.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/gates.py'),run_name='__main__')
