import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parent;os.environ['SKIP_PILOT_RENDERS']='1'
for n in ['finish_pilot.py','geometry_finish.py','texture_return.py','dense_gates.py']:runpy.run_path(str(p/n),run_name='__main__')
