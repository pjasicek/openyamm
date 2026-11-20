import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('reweight_motion.py')
run('ground_tail.py')
run('scan_deformation.py',P/'work/rig_grounded.blend')
run('g6_contacts.py',P/'work/rig_grounded.blend','Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget')
run('g6_head_clearance.py',P/'work/rig_grounded.blend','Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget')
