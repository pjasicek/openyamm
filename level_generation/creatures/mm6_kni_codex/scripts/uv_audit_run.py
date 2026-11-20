import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.argv=['uv','--','work/production_body.blend','meshy/retexture_v1','work/textured_master.blend'];runpy.run_path(str(P/'scripts/uv_transfer_audit.py'),run_name='__main__')
