import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.argv=['examine_parts.py','--',str(P/'meshy/skull_smart_topology_v1/model_urls_glb.glb'),'skull_v1']
runpy.run_path(str(P/'scripts/examine_parts.py'),run_name='__main__')
