import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for level in [1,2,3]:
 os.environ['LCH_BAKE_LEVEL']=str(level);runpy.run_path(str(P/'scripts/round2_bake_lod.py'),run_name='__main__')
