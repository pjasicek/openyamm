from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];root=p.parents[2]
sys.argv=[str(root/'tools/build_actor_lods.py'),'--',str(p/'export/mm8_m444_runtime_lod0.glb'),str(p/'export/mm8_m444_lods.glb'),'--mesh-node','Smuggler','--max-influences','8'];runpy.run_path(str(root/'tools/build_actor_lods.py'),run_name='__main__')
