import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
sys.argv=['build_actor_lods.py','--',str(p/'export/mm6_pfem_runtime_lod0.glb'),str(p/'export/mm6_pfem_lods.glb'),'--mesh-node','Peasant','--max-influences','4']
runpy.run_path(str(root/'tools/build_actor_lods.py'),run_name='__main__')
