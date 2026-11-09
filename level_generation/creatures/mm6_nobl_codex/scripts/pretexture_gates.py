import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('build_sword.py');run('export_review.py')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
run('g6_contacts.py',[p/'review/viewer/mm6_nobl_clay.glb',*roles])
run('g6_head_clearance.py',[p/'work/rig_v8.blend',*roles])
run('g6_sword_mesh.py',[p/'review/viewer/mm6_nobl_clay.glb'])
run('render_strain.py')
