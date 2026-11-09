import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
for script,args in [('motion_pose_audit.py',[]),('g5_hand_stretch.py',['work/motion_fit.blend','Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'])]:
 sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
