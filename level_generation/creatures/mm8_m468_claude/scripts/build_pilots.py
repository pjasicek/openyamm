from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_fix.py')
mx=root/'anim_library/mixamo'
run('retarget_mixamo.py',p/'work/rig_owned.blend',p/'work/pilot_mixamo.blend',f'{mx}/Mutant Breathing Idle.fbx:Standing',f'{mx}/Mutant Walking.fbx:Walking',f'{mx}/Zombie Attack (1).fbx:Attack')
os.environ['FRADIUS']='.025';run('finger_weights.py',p/'work/pilot_mixamo.blend',p/'work/pilot_fingers.blend')
run('foot_level.py',p/'work/pilot_fingers.blend',p/'work/pilot_feet.blend','Standing','Walking:const','Attack')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
run('twist_bones.py',p/'work/pilot_feet.blend',p/'work/pilot_raw.blend')
