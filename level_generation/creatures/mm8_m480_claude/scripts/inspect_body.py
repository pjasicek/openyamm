from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];s=p/'scripts/examine_parts.py'
sys.argv=[str(s),'--',str(p/'meshy/body_v1/model_urls_glb.glb'),'body_v1']
runpy.run_path(str(s),run_name='__main__')
