"""Use reviewed auto-rig centres, with wrists at the actual exposed-hand cuffs."""
import json, runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
J = json.loads((P/'work/meshy_joints.json').read_text())
# The sleeve and boot silhouettes invalidate the generic narrowest-ring estimates.
J['joints']['L_Hand'] = [0.4093137, -0.03557282, 1.0254406]
J['joints']['R_Hand'] = [-0.41272852, -0.03562063, 1.0277961]
J['selection'] = 'Meshy centres reviewed in front/profile X-rays; wrists replaced by measured native hand-cuff boundary centres. Ring knees/ankles rejected: selected folds and boot shafts.'
(P/'work/joints_final.json').write_text(json.dumps(J,indent=2)+'\n')
def run(name, *args):
    sys.argv = [name, '--', *[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/name), run_name='__main__')
run('build_rig.py')
run('fit_fingers.py', P/'work/rig_v1.blend')
run('finger_joints.py', P/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py', P/'work/rig_v1.blend')
for side in ('R','L'):
    run('hand_xray.py', P/'work/rig_v1.blend', side, P/f'review/fingers_{side}')
