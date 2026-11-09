from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ['export.py','build_runtime.py','verify_delivery.py']:
    runpy.run_path(str(p/script),run_name='__main__')
