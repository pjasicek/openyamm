from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
sys.argv=['build_actor_lods.py','--',str(P/'export/mm8_m484_runtime_lod0.glb'),str(P/'export/mm8_m484_lods.glb'),'--mesh-node','M484','--max-influences','4']
runpy.run_path(str(P.parents[2]/'tools/build_actor_lods.py'),run_name='__main__')
