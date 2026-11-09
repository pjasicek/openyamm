import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.argv=['transfer','--','work/texture_weighted.blend','meshy/body_retexture_v1','work/textured_uv.blend'];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
