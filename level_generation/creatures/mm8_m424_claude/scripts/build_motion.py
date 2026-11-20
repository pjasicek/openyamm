import runpy, sys, os
from pathlib import Path
P=Path(__file__).resolve().parents[1]; R=P.parents[2]
def run(n,*args):
    sys.argv=[n,'--',*[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_fix.py')
L=R/'anim_library/humanoid_set'
run('retarget.py',P/'work/rig_owned.blend',P/'work/rig_motion_set.blend',
    f'{L}/Relax.glb:RelaxIdle:Standing',f'{L}/Relax.glb:RelaxWalkForward:Walking',
    f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{L}/Unarmed.glb:UnarmedDeath1:Death',
    f'{L}/1Hand.glb:DaggerAttackR2:GripRef')
run('retarget_mixamo.py',P/'work/rig_motion_set.blend',P/'work/rig_motion_mixamo.blend',
    f'{R}/anim_library/mixamo/Standard Run.fbx:Running')
run('foot_level.py',P/'work/rig_motion_mixamo.blend',P/'work/rig_feet.blend','Standing','Walking:const','Hit','Death:until=8')
os.environ['RUN_STRIDE']='1.8'
run('run_fit.py',P/'work/rig_feet.blend',P/'work/rig_run.blend')
os.environ['FA']='0.6'; os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',P/'work/rig_run.blend',P/'work/rig_twist.blend')
os.environ['FRADIUS']='0.014'
run('finger_weights.py',P/'work/rig_twist.blend',P/'work/rig_fingers.blend')
