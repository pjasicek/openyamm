from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['reduce_rigged.py','export_reduced.py','run_reduced_gates.py','export_uploads.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
