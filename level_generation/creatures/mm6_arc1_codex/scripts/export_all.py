import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for n in ['export_runtime.py','build_lods.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
