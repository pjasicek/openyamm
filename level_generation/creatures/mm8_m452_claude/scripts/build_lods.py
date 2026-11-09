import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];root=P.parents[2]
sys.argv=[__file__,'--',str(P/'export/mm8_m452_materials.glb'),str(P/'export/mm8_m452_lods.glb'),'--mesh-node','Rat','--max-influences','4']
runpy.run_path(str(root/'tools/build_actor_lods.py'),run_name='__main__')
