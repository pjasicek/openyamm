from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
def run(name,args):
    sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('finger_weights.py',[p/'work/rig_v1.blend',p/'work/rig_fingers.blend'])
run('retarget.py',[p/'work/rig_fingers.blend',p/'work/motion_base.blend',
    'anim_library/humanoid_set/Armed.glb:ArmedIdle:Standing',
    'anim_library/humanoid_set/Armed.glb:ArmedWalk:Walking',
    'anim_library/humanoid_set/Armed.glb:ArmedRunForward:Running',
    'anim_library/humanoid_set/1Hand.glb:SwordAttackR1:Attack',
    'anim_library/humanoid_set/Armed.glb:ArmedGetHitF1:Hit',
    'anim_library/humanoid_set/Armed.glb:ArmedDeath1:Death',
    'anim_library/humanoid_set/Armed.glb:ArmedIdleAlert1:Fidget'])
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',[p/'work/motion_base.blend',p/'work/motion_twist.blend'])
run('grip_from_source.py',['anim_library/humanoid_set/Armed.glb','ArmedIdle:0','ArmedWalk:0'])
