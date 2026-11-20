import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['polish_motion.py','assemble_pilot.py','contact_pilot.py','gate_clothing.py']:runpy.run_path(str(P/name),run_name='__main__')
