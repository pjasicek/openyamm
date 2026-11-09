import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
clips=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
run('scan_deformation.py',P/'work/master.blend')
run('g6_contacts.py',P/'work/master.blend',*clips)
run('g6_head_clearance.py',P/'work/master.blend',*clips)
run('equipment_gate.py')
run('render_master.py')
