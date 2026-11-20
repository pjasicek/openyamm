from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2];tool=repo/'tools/build_actor_lods.py'
sys.argv=[str(tool),'--',str(p/'export/mm8_m476_prepared.glb'),str(p/'export/mm8_m476_lods.glb'),'--mesh-node','Troll']
runpy.run_path(str(tool),run_name='__main__')
