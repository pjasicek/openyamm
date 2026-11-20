import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['rebake_soft_seams_run.py','finish_lod3.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
