from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ('inspect_prop_topology.py','refine_grip.py'):runpy.run_path(str(p/script),run_name='__main__')
