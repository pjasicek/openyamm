import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods.py',str(p/'export/mm8_m500_runtime_lod0.glb'),str(p/'export/mm8_m500_lods.glb'),'--mesh-node','Body','--max-influences','4']
runpy.run_path('tools/build_actor_lods.py',run_name='__main__')
