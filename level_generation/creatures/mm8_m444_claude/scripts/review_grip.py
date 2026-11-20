from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1];os.environ.update(R_HANDLE='0.012',GRIP_TILT='0',GRIP_RENDER=str(p/'review/grip'))
sys.argv=[str(p/'scripts/grip_solve.py'),'--',str(p/'work/rig_v4f.blend'),'GripRef','8'];runpy.run_path(str(p/'scripts/grip_solve.py'),run_name='__main__')
