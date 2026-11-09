from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('build_rig.py')
run('weights_fix.py')
os.environ['FRADIUS']='.035'
run('finger_weights.py',p/'work/rig_owned.blend',p/'work/rig_fingers.blend')
run('retarget.py',p/'work/rig_fingers.blend',p/'work/pilot_raw.blend','anim_library/humanoid_set/Relax.glb:RelaxIdle:Standing','anim_library/humanoid_set/Unarmed.glb:UnarmedAttackR2:Attack')
run('retarget_mixamo.py',p/'work/pilot_raw.blend',p/'work/pilot_raw.blend','anim_library/mixamo/Orc Walk.fbx:Walking')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
run('twist_bones.py',p/'work/pilot_raw.blend',p/'work/pilot_twist.blend')
run('finish_pilot.py')
