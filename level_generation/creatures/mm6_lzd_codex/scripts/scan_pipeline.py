import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_lizard.py')
run('apply_grip.py',P/'work/rig_v5.blend',P/'work/rig_v6.blend')
run('scan_deformation.py',P/'work/rig_v6.blend')
run('g6_contacts.py',P/'work/rig_v6.blend','Standing','Walking','Running','Attack','Hit','Death')
run('g6_head_clearance.py',P/'work/rig_v6.blend','Standing','Walking','Running','Attack','Hit','Death')
