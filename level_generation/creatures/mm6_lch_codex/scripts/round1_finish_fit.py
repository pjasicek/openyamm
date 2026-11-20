import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
os.environ['LCH_LOD']='3';runpy.run_path(str(P/'scripts/round1_adaptive_subpixel.py'),run_name='__main__')
os.environ['LCH_LOD']='1';runpy.run_path(str(P/'scripts/round1_adaptive_fine.py'),run_name='__main__')
