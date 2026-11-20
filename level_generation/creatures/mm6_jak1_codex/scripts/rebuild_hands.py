import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['refine_hand_mesh.py','build_jackal_rig.py','prepare_animation.py','inspect_hands.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
