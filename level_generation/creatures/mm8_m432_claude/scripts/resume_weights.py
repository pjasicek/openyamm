import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
for script,src,out in [('weights_fix.py','rig_twist.blend','rig_weighted.blend'),('finger_weights.py','rig_weighted.blend','rig_fingers.blend')]:
 sys.argv=[script,'--',str(P/'work'/src),str(P/'work'/out)]
 os.environ['FRADIUS']='0.014'
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')

os.environ['GRIP_SIDE']='L'
sys.argv=['grip_from_source.py','--',str(P.parents[2]/'anim_library/humanoid_set/2Hand Sword.glb'),'2HandSwordIdle:0']
runpy.run_path(str(P/'scripts/grip_from_source.py'),run_name='__main__')
for side in ('R','L'):
 os.environ['GRIP_SIDE']=side;os.environ['R_HANDLE']='0.012'
 os.environ['GRIP_RENDER']=str(P/f'review/grip_{side}')
 sys.argv=['grip_solve.py','--',str(P/'work/rig_fingers.blend'),'GripRef','0']
 runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
