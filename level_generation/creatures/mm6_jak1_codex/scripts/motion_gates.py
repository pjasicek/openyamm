import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('trace_export.py',[P/'export/mm6_jak1_runtime_lod0.glb'])
run('g5_hand_stretch.py',[P/'work/production_body.blend','Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'])
run('g6_staff_mesh.py',[P/'export/mm6_jak1_runtime_lod0.glb'])
run('blow_gate.py')
