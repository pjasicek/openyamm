from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
run('base_weights.py');run('author_idle.py')
run('retarget.py',p/'work/idle.blend',p/'work/motion_a.blend','anim_library/humanoid_set/Armed.glb:ArmedWalk:Walking','anim_library/humanoid_set/Unarmed.glb:UnarmedRunForward:Running','anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1:Death')
os.environ['PLANT_FROM']='Standing'
run('retarget.py',p/'work/motion_a.blend',p/'work/motion_base.blend','anim_library/humanoid_set/Unarmed.glb:UnarmedCastDualAttack2:Attack','anim_library/humanoid_set/Unarmed.glb:UnarmedCastDualAttack2:Cast','anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1:Hit')
os.environ.pop('PLANT_FROM')
os.environ['FA_RAMP']='.15,.85';os.environ['FA']='.6'
run('twist_bones.py',p/'work/motion_base.blend',p/'work/motion_twist.blend')
