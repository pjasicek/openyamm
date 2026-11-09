import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods.py',str(p/'export/mm6_med_runtime_lod0.glb'),str(p/'export/mm6_med_lods.glb'),'--mesh-node','Body']
runpy.run_path('tools/build_actor_lods.py',run_name='__main__')
