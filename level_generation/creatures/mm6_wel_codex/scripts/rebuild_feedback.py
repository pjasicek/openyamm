import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['add_foam.py','water_surface_v2.py','poseidon_v2.py','export_water.py','verify_reduced.py']:
 print('FEEDBACK REBUILD',name,flush=True);runpy.run_path(str(P/name),run_name='__main__')
