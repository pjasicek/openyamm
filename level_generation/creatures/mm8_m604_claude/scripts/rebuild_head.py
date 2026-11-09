from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['geometry_finish.py','export_uploads.py','audit_geometry.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
