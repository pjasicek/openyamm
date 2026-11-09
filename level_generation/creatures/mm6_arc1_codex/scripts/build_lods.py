import sys,runpy,bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['build_actor_lods.py','--',str(P/'export/mm6_arc1_lod0.glb'),str(P/'export/mm6_arc1_lods.glb'),'--mesh-node','Archer'];runpy.run_path(str(P.parents[2]/'tools/build_actor_lods.py'),run_name='__main__')
