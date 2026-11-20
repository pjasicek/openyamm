import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for layer in ['UVMap','HeadUV']:
 os.environ['ARC1_UV_LAYER']=layer;runpy.run_path(str(P/'scripts/uv_gate.py'),run_name='__main__')
