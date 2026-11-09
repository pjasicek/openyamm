import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('finger_weights.py',['work/rig_weighted.blend','work/rig_weighted_fingers.blend'])
os.environ['R_HANDLE']='0.013';os.environ['GRIP_RENDER']=str(P/'review/grip');run('grip_solve.py',['work/rig_weighted_fingers.blend','GripRef',8])
run('apply_grip.py',['work/rig_weighted_fingers.blend','work/rig_grip.blend'])
run('inspect_hands.py')
