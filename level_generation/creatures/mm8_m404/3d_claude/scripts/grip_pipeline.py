import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_body.py',p/'work/rig_v2.blend',p/'work/rig_weighted.blend')
run('finger_weights.py',p/'work/rig_weighted.blend',p/'work/rig_fingers.blend')
for side in ('R','L'):
 os.environ['GRIP_SIDE']=side;os.environ['R_HANDLE']='0.016';os.environ['GRIP_RENDER']=str(p/('review/grip_'+side));os.environ['GRIP_SCALE']='0.32'
 run('grip_solve.py',p/'work/rig_fingers.blend','Standing',0)
