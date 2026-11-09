import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
os.environ['R_HANDLE']='0.013';os.environ['GRIP_PALM_FLIP']='1';os.environ['GRIP_RENDER']=str(P/'review/grip')
sys.argv=['grip_solve','--','work/rig_weighted_fingers.blend','GripRef','8'];runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')

sys.argv=['apply','--','work/rig_weighted_fingers.blend','work/rig_grip.blend'];runpy.run_path(str(P/'scripts/apply_grip.py'),run_name='__main__')
sys.argv=['g5','--','work/rig_grip.blend','Standing'];runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
