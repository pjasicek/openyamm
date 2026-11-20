from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('reduce_rigged.py',p/'work/clearance_v1.blend',p/'work/reduced_v1.blend')
run('export_uploads.py')
run('g5_hand_stretch.py',p/'work/reduced_v1.blend','Standing','Walking','Hit','Fidget','Death')
run('g6_contacts.py',p/'work/reduced_v1.blend','Standing','Walking','Hit','Fidget','Death')
