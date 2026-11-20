import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['review3_approach_fit.py','review3_hand_weights.py','review3_coarse_grip_surface.py','review3_far_feathers.py','review2_reload.py']:runpy.run_path(str(p/n),run_name='__main__')
