import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];B=P/'work/motion_reduced.blend'
os.environ['M632_CHECK_BLEND']='work/motion_reduced.blend'
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
acts=['Standing','Walking','Running','Attack','Hit','Death','Fidget','Dead']
run('g4_weights.py',B,'reduced','Standing:0','Walking:24','Running:22','Attack:150','Attack:166','Hit:24','Death:160','Fidget:75','Dead:0')
run('g5_hand_stretch.py',B,*acts)
os.environ['STEP']='1';run('sole_probe.py',B,*acts)
run('jerk_probe.py',B,*acts)
run('hand_review.py');run('grip_contacts.py');run('contacts.py')
for view in ('front','left','back'):
 run('pilot_sheet.py',B,P/f'review/reduced_{view}',view,7,*acts)
