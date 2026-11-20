from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_fix.py')
lib=root/'anim_library/humanoid_set'
run('retarget.py',p/'work/rig_owned.blend',p/'work/pilot_set.blend',f'{lib}/Armed.glb:ArmedIdle:Standing',f'{lib}/1Hand.glb:MaceAttackR1:GripRef')
mx=root/'anim_library/mixamo'
run('retarget_mixamo.py',p/'work/pilot_set.blend',p/'work/pilot_mixamo.blend',f'{mx}/Orc Walk.fbx:Walking',f'{mx}/Standing Melee Attack Downward.fbx:Attack')
run('foot_level.py',p/'work/pilot_mixamo.blend',p/'work/pilot_feet.blend','Standing','Walking:const','Attack')
run('author_carry.py',p/'work/pilot_feet.blend',p/'work/pilot_carried.blend','Standing:.15','Walking:.30')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',p/'work/pilot_carried.blend',p/'work/pilot_twist.blend')
os.environ['FRADIUS']='.035'
run('finger_weights.py',p/'work/pilot_twist.blend',p/'work/pilot_fingers.blend')
run('smooth_thumb_weights.py')
os.environ['R_HANDLE']='.025';os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',p/'work/pilot_fingers.blend','GripRef','8')
run('apply_grip.py',p/'work/pilot_fingers.blend',p/'work/pilot_grip.blend')
