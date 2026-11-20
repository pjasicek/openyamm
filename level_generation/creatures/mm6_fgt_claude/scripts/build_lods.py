from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.argv=['build_actor_lods.py','--',str(p/'export/mm6_fgt_runtime_lod0.glb'),str(p/'export/mm6_fgt_lods.glb'),'--mesh-node','Thug']
runpy.run_path(str(repo/'tools/build_actor_lods.py'),run_name='__main__')
