"""Driver (after stage_rig.py): ownership weights, dress chains, retarget the selected clips (RelaxWalkForward chosen
over RelaxWalkFemale, whose strong hip sway and shoulder lean read as a sashay next to the calm native walk; plus the
source dagger grip reference), the Mixamo run, foot levelling, run fit, twist bones and
finger weights. One Blender process."""
import runpy, sys, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]; R = P.parents[2]
def run(n, *args):
    sys.argv = [n, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
W = P / 'work'; L = R / 'anim_library/humanoid_set'
run('weights_fix.py')
run('dress_rig.py')
run('retarget.py', W / 'rig_dress.blend', W / 'rig_motion_set.blend',
    f'{L}/Relax.glb:RelaxIdle:Standing', f'{L}/Relax.glb:RelaxWalkForward:Walking',
    f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit', f'{L}/Unarmed.glb:UnarmedDeath1:Death',
    f'{L}/1Hand.glb:DaggerAttackR2:GripRef')
run('retarget_mixamo.py', W / 'rig_motion_set.blend', W / 'rig_motion_mixamo.blend',
    f'{R}/anim_library/mixamo/Standard Run.fbx:Running')
run('foot_level.py', W / 'rig_motion_mixamo.blend', W / 'rig_feet.blend', 'Standing', 'Walking:const', 'Hit', 'Death:until=8')
os.environ['RUN_STRIDE'] = os.environ.get('RUN_STRIDE', '1.6')
os.environ['RUN_HEEL'] = os.environ.get('RUN_HEEL', '0.5')      # dress: damped heel kick (review 2026-10-19)
run('run_fit.py', W / 'rig_feet.blend', W / 'rig_run.blend')
os.environ['FA'] = '0.6'; os.environ['FA_RAMP'] = '0.15,0.85'
run('twist_bones.py', W / 'rig_run.blend', W / 'rig_twist.blend')
os.environ['FRADIUS'] = '0.014'
run('finger_weights.py', W / 'rig_twist.blend', W / 'rig_fingers.blend')
for view in ('front', 'left'):
    run('clip_sheet.py', W / 'rig_fingers.blend', P / f'review/motion_{view}', view, 6,
        'Standing', 'Walking', 'Running', 'Hit', 'Death')
