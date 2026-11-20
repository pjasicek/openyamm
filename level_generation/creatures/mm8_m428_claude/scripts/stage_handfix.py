"""Driver for the right-hand review fix (2026-10-19, user: the dagger hand's palm faced outward): re-solve the fist
on the palm side (grip_solve.py), apply it, re-solve the civilian carry (Standing, Walking) with the palm toward the thigh (author_carry.py, armik k_palm), redo the twist
bake, then everything downstream through stage_refine.py (fidget, timing, wrists, twist, dagger, dress cloth,
actions into the textured master, fix_cuffs, LOD0 export)."""
import runpy, sys, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(n, *args):
    sys.argv = [n, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
W = P / 'work'
os.environ['R_HANDLE'] = '0.010'; os.environ['GRIP_RENDER'] = str(P / 'review/grip')
run('grip_solve.py', W / 'rig_refined.blend', 'GripRef', 0)
run('apply_grip.py', W / 'rig_refined.blend', W / 'rig_refined_grip.blend')
run('author_carry.py', W / 'rig_refined_grip.blend', W / 'rig_carry.blend', 'Standing:0.3', 'Walking:0.35')
os.environ['FA'] = '0.6'; os.environ['FA_RAMP'] = '0.15,0.85'
run('twist_bones.py', W / 'rig_carry.blend', W / 'rig_carry_twist.blend')
sys.argv = ['stage_refine.py']
runpy.run_path(str(P / 'scripts/stage_refine.py'), run_name='__main__')
