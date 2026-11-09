import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p)
sys.argv=['examine_parts.py','--','meshy/body_round2_smart/model_urls_glb.glb','round2/raw']
runpy.run_path(str(p/'scripts/examine_parts.py'),run_name='__main__')
