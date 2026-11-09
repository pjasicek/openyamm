import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
for name in ['fit_shoulder_weights.py','export_runtime.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
