import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['make_props.py','finalize_motion.py','equipment_floor.py','export_final_lods.py','final_physics.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
