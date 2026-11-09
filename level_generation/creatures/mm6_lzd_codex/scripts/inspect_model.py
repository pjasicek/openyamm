import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
runpy.run_path(str(P/'scripts/source_rom.py'),run_name='__main__')
sys.argv=['examine_parts.py','--','meshy/smart_topology_v1/model_urls_glb.glb','st_v1']
runpy.run_path(str(P/'scripts/examine_parts.py'),run_name='__main__')
