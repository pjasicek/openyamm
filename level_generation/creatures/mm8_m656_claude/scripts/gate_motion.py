import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));B=P/'work/master_rig.blend'
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
A=['Standing','Walking','Running','Attack','Hit','Fidget','Death']
run('g5_hand_stretch.py',B,*A)
run('g4_weights.py',B,'full','Standing:0','Walking:5','Running:8','Attack:26','Attack:33','Attack:40','Hit:8','Fidget:25','Fidget:42','Death:42')
run('g6_head_clearance.py',B,*A)
os.environ['STEP']='0.5';run('sole_probe.py',B,*A)
run('g6_contacts.py',B,*A)
for view in ('front','left','three_quarter'):run('clip_sheet.py',B,P/f'review/full_{view}',view,7,*A)
