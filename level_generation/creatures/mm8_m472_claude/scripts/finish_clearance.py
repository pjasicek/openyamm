from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['garment_sim.py','polish_weights.py','finish_geometry.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
runpy.run_path(str(p/'scripts/check_deformation.py'),init_globals={'INPUT_BLEND':'rig_gated.blend'},run_name='__main__')
runpy.run_path(str(p/'scripts/source_jerk.py'),run_name='__main__')
