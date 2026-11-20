import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['weight_probe.py','rig_gates.py']:
 sys.argv=[n];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
