from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1]
os.environ['R_HANDLE']='0.014';os.environ['GRIP_RENDER']=str(p/'review/grip');os.environ['GRIP_SCALE']='0.30'
sys.argv=['grip_solve','--',str(p/'work/motion_adapted.blend'),'Standing','0']
runpy.run_path(str(p/'scripts/grip_solve.py'),run_name='__main__')
sys.argv=['apply_grip','--',str(p/'work/motion_adapted.blend'),str(p/'work/motion_grip.blend')]
runpy.run_path(str(p/'scripts/apply_grip.py'),run_name='__main__')
