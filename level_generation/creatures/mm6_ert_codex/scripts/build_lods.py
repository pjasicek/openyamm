import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods','--',str(P/'export/mm6_ert_runtime_lod0.glb'),str(P/'export/mm6_ert_lods.glb'),'--mesh-node','EarthElemental']
runpy.run_path('tools/build_actor_lods.py',run_name='__main__')
