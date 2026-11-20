import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['make_props.py','arm_clearance.py','finalize_motion.py','equipment_floor.py','scabbard_sweep.py','probe_mount.py']:
 runpy.run_path(str(P/n),run_name='__main__')
