"""Driver (after stage_joints.py): source-frame rig, connectivity finger fit, finger joints, rig rebuilt with the
mesh knuckle line, hand frame check and hand X-rays (one Blender process)."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(name, *args):
    sys.argv = [name, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / name), run_name='__main__')
fj = P / 'work/finger_joints.json'
if fj.exists():
    fj.unlink()
run('compose_joints.py')
run('build_rig.py')
run('fit_fingers.py', P / 'work/rig_v1.blend')
run('finger_joints.py', P / 'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py', P / 'work/rig_v1.blend')
for side in ('R', 'L'):
    run('hand_xray.py', P / 'work/rig_v1.blend', side, P / f'review/fingers_{side}')
