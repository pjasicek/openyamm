import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['examine_parts.py','--',str(P/'meshy/smart_topology_v1/model_urls_glb.glb'),'st_v1']
runpy.run_path(str(P/'scripts/examine_parts.py'),run_name='__main__')
