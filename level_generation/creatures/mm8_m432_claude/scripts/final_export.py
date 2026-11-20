from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
for name in ['check_uv.py','export_runtime.py','verify_export.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
