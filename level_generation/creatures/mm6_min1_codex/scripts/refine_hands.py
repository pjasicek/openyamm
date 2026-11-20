import bpy,sys,os,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
sys.argv=['finger_weights.py','--','work/rig_v3.blend','work/rig_v4.blend'];runpy.run_path(str(P/'scripts/finger_weights.py'),run_name='__main__')
for side in ['R','L']:
 os.environ['HAND_SIDE']=side;os.environ['GRIP_RENDER']=str(P/f'review/grip_{side}')
 sys.argv=['grip_solve.py','--','work/rig_v4.blend','Standing','0'];runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
shutil.copyfile(P/'work/grip_pose_R.json',P/'work/grip_pose.json')
sys.argv=['apply_grip.py','--','work/rig_v4.blend','work/rig_v5.blend'];runpy.run_path(str(P/'scripts/apply_grip.py'),run_name='__main__')
sys.argv=['g5_hand_stretch.py','--','work/rig_v5.blend','Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget'];runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
