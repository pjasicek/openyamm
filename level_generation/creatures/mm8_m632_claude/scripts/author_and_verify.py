import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('author_motion.py','grip_probe.py','verify_pilot.py'):runpy.run_path(str(P/name),run_name='__main__')
