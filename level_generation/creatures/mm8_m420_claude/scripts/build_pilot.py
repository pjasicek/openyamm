from pathlib import Path
import os,sys,runpy
P=Path(__file__).resolve().parents[1];W=P/'work';ROOT=P.parents[2];sys.path.insert(0,str(P/'scripts'))
def run(n,*args):
    sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
M=ROOT/'anim_library/mixamo';L=ROOT/'anim_library/humanoid_set'
run('weights_fix.py',W/'rig_v1.blend',W/'weighted.blend')
os.environ['FRADIUS']='0.014'
run('finger_weights.py',W/'weighted.blend',W/'weighted_fingers.blend')
run('retarget_mixamo.py',W/'weighted_fingers.blend',W/'locomotion.blend',f'{M}/Standard Idle.fbx:Standing',f'{M}/Walk.fbx:Walking',f'{M}/Standard Run.fbx:Running')
run('retarget.py',W/'locomotion.blend',W/'source_motion.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedCastRAttack1:AttackSource:plant',f'{L}/Unarmed.glb:UnarmedGetHitF1:HitSource:plant',f'{L}/Unarmed.glb:UnarmedDeath1:Death')
run('grip_solve.py',W/'source_motion.blend','GripRef','8')
run('author_carry.py',W/'source_motion.blend',W/'carry.blend','Standing:0.1','Walking:0.18','Running:0.18')
run('apply_grip.py',W/'carry.blend',W/'pilot.blend')
