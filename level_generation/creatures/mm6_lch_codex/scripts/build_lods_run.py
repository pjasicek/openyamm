import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['build_actor_lods.py','--',str(P/'export/mm6_lch_runtime_lod0.glb'),str(P/'export/mm6_lch_lods.glb'),'--mesh-node','Lich']
runpy.run_path(str(P.parents[2]/'tools/build_actor_lods.py'),run_name='__main__')
