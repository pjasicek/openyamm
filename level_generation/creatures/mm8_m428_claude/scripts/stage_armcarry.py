"""Driver for the arm-carry review (2026-10-19, user: the dagger arm should hang beside her body as in the native
frames): civilian carry re-solved with carry.json (Standing, Walking, Running), twist bake, then stage_refine.py
(fidget, Hit/Death blends from the new Standing, wrists, dress cloth, actions into the textured master, LOD0 export).
The fist (grip_pose.json) is not re-solved."""
import runpy, sys, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(n, *args):
    sys.argv = [n, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
W = P / 'work'
run('author_carry.py', W / 'rig_refined_grip.blend', W / 'rig_carry.blend', 'Standing:0.3', 'Walking:0.35', 'Running:0.45')
os.environ['FA'] = '0.6'; os.environ['FA_RAMP'] = '0.15,0.85'
run('twist_bones.py', W / 'rig_carry.blend', W / 'rig_carry_twist.blend')
sys.argv = ['stage_refine.py']
runpy.run_path(str(P / 'scripts/stage_refine.py'), run_name='__main__')
