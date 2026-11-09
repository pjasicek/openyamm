import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for s in ['remove_neck_ring.py','texture_prepare.py']:runpy.run_path(str(P/'scripts'/s),run_name='__main__')
