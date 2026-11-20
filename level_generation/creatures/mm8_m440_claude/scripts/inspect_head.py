from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=['examine_head.py','--',str(p/'meshy/head_geometry_v1/model_urls_glb.glb'),'head_v1']
runpy.run_path(str(p/'scripts/examine_head.py'),run_name='__main__')
