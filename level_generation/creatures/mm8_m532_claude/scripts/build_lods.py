from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];repo=P.parents[2]
sys.argv=['build_actor_lods.py',str(P/'export/mm8_centaur_prepared.glb'),str(P/'export/mm8_centaur_lods.glb'),'--mesh-node','Body','--max-influences','4']
runpy.run_path(str(repo/'tools/build_actor_lods.py'),run_name='__main__')
