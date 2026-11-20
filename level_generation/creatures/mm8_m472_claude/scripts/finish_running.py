from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['time_and_ground.py','garment_sim.py','polish_weights.py','prepare_texture_geometry.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
