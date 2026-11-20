import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods.py','--',str(P/'export/mm6_dwa1_runtime_lod0.glb'),str(P/'export/mm6_dwa1_lods.glb'),'--mesh-node','Dwarf']
runpy.run_path(str(P.parents[2]/'tools/build_actor_lods.py'),run_name='__main__')
