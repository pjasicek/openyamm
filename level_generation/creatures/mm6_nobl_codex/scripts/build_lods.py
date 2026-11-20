import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.argv=['lods','--',str(p/'export/mm6_nobl_runtime_lod0.glb'),str(p/'export/mm6_nobl_lods.glb'),'--mesh-node','Swordsman']
runpy.run_path(str(repo/'tools/build_actor_lods.py'),run_name='__main__')
