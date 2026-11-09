import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.argv=['lod','--',str(P/'export/mm6_kni_runtime_lod0.glb'),str(P/'export/mm6_kni_lods.glb'),'--mesh-node','KnightPlate'];runpy.run_path(str(P.parents[2]/'tools/build_actor_lods.py'),run_name='__main__')
