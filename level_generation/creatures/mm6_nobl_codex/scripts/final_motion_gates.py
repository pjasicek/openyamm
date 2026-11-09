import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
run('loop_audit.py')
run('g6_contacts.py',[p/'export/mm6_nobl_runtime_lod0.glb',*roles])
run('g6_sword_mesh.py',[p/'export/mm6_nobl_runtime_lod0.glb'])
run('g6_head_clearance.py',[p/'work/rig_v15.blend',*roles])
