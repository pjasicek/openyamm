import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);L=ROOT/'anim_library/humanoid_set';MX=ROOT/'anim_library/mixamo'
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('hand_frame_check.py',['work/rig_v1.blend'])
run('retarget.py',['work/rig_fingers.blend','work/source_actions.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{L}/Armed.glb:ArmedDeath1:Death'])
run('retarget_mixamo.py',['work/source_actions.blend','work/source_actions_mixamo.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Standing Idle 02 Looking.fbx:Fidget:plant'])
run('retarget.py',['work/source_actions_mixamo.blend','work/source_actions_all.blend',f'{L}/1Hand.glb:SpearAttackR1:Attack:plant',f'{L}/1Hand.glb:SpearAttackR1:AttackFull',f'{L}/Armed.glb:ArmedCastLAttack1:Cast:plant',f'{L}/Armed.glb:ArmedCastLAttack1:CastFull'])
run('twist_bones.py',['work/source_actions_all.blend','work/rig_twist.blend'])
run('body_weights.py')
os.environ['R_HANDLE']='0.016';os.environ['GRIP_RENDER']=str(P/'review/grip');run('grip_solve.py',['work/rig_weighted.blend','GripRef',8])
run('apply_grip.py',['work/rig_weighted.blend','work/rig_grip.blend'])
