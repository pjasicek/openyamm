from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
os.chdir(p.parents[2])
sys.argv=[str(p/'scripts/examine_parts.py'),'--',str(p/'meshy/smart_topology_v2/model_urls_glb.glb'),'st_v1']
runpy.run_path(sys.argv[0],run_name='__main__')
