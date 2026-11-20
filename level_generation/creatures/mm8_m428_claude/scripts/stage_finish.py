"""Driver (after stage_motion.py): reduction after weighting, refined knuckle weights, dagger fist (grip from the
source dagger attack), civilian dagger carry, twist, authored fidget, timing/floor, wrist roll, twist, dagger bone,
dress cloth bake, review sheets and gates. One Blender process."""
import runpy, sys, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(n, *args):
    sys.argv = [n, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
W = P / 'work'
run('grip_from_source.py', P.parents[2] / 'anim_library/humanoid_set/1Hand.glb', 'DaggerAttackR2:0', 'DaggerAttackR3:12')
run('reduce_rigged.py')
run('refine_weights.py')
os.environ['R_HANDLE'] = '0.010'; os.environ['GRIP_RENDER'] = str(P / 'review/grip')
run('grip_solve.py', W / 'rig_refined.blend', 'GripRef', 0)
run('apply_grip.py', W / 'rig_refined.blend', W / 'rig_refined_grip.blend')
run('author_carry.py', W / 'rig_refined_grip.blend', W / 'rig_carry.blend', 'Standing:0.3', 'Walking:0.35')
os.environ['FA'] = '0.6'; os.environ['FA_RAMP'] = '0.15,0.85'
run('twist_bones.py', W / 'rig_carry.blend', W / 'rig_carry_twist.blend')
run('author_fidget.py')
run('finish_timing.py')
run('settle_wrists.py')
run('twist_bones.py', W / 'rig_wrists.blend', W / 'rig_timed_twist.blend')
run('dagger.py')
run('dress_sim.py', W / 'rig_props.blend', W / 'rig_sim.blend')
for view in ('front', 'left', 'back'):
    run('clip_sheet.py', W / 'rig_sim.blend', P / f'review/clips_{view}', view, 6,
        'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
run('g5_hand_stretch.py', W / 'rig_sim.blend', 'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
run('sole_probe.py', W / 'rig_sim.blend', 'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
