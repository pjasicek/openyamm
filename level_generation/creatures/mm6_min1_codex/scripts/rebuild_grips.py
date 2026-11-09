import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
(P/'work/finger_joints.json').unlink(missing_ok=True)
for s in ['build_minotaur_rig.py','animate_base.py','solve_grips.py']:
 runpy.run_path(str(P/'scripts'/s),run_name='__main__')
