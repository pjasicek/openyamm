import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['probe_edges.py','head_upload.py','audit_geometry.py']:runpy.run_path(str(p/f),run_name='__main__')
