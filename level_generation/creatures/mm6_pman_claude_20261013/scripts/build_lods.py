import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods','--',str(P/'export/mm6_pman_v2_runtime_lod0.glb'),str(P/'export/mm6_pman_v2_lods.glb'),'--mesh-node','Peasant']
runpy.run_path('tools/build_actor_lods.py',run_name='__main__')
