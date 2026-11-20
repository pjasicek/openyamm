import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['couple_sword.py','arm_planes.py','finish_motion.py','assemble.py','contact_probe.py']:runpy.run_path(str(P/name),run_name='__main__')
