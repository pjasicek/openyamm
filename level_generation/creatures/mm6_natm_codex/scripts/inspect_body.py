from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1];os.chdir(p)
sys.argv=['examine_parts.py','--','meshy/body_geometry_v1/model_urls_glb.glb','st_v1']
runpy.run_path(str(p/'scripts/examine_parts.py'),run_name='__main__')
