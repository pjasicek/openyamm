import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['viewer_tiers.py','update_viewer_manifest.py']:runpy.run_path(str(p/n),run_name='__main__')
