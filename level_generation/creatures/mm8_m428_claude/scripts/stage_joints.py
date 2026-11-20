"""Driver: source rest frames/proportions, Meshy joints, our composed joints and X-ray (one Blender process)."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; R = P.parents[2]
SET = R / 'anim_library/humanoid_set/Relax.glb'
def run(name, *args):
    sys.argv = [name, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / name), run_name='__main__')
if not (P / 'work/source_rest.json').exists():
    run('source_rest.py', SET); run('proportions.py', 'source', SET)
run('meshy_joints.py', P / 'meshy/rig_v1/result_rigged_character_glb_url.glb', P / 'work/step1.blend')
run('compose_joints.py')
run('joint_xray.py', P / 'work/step1.blend', 'Body', P / 'work/joints_final.json', P / 'review/xray_final', P / 'work/meshy_joints.json')
