import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parent;os.environ['SKIP_PILOT_RENDERS']='1'
for n in ['finish_pilot.py','geometry_finish.py','dense_gates.py','cloth_topology.py','attack_probe.py']:runpy.run_path(str(p/n),run_name='__main__')
