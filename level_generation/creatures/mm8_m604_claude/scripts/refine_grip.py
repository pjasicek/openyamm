from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
os.environ['R_HANDLE']='0.016';os.environ['GRIP_RENDER']=str(p/'review/grip_v2');os.environ['GRIP_SCALE']='0.28'
s=p/'scripts/grip_solve.py';sys.argv=[str(s),'--',str(p/'work/fingered.blend'),'Attack','0'];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/apply_grip.py';sys.argv=[str(s),'--',str(p/'work/fingered.blend'),str(p/'work/pilot.blend')];runpy.run_path(str(s),run_name='__main__')
runpy.run_path(str(p/'scripts/inspect_head.py'),run_name='__main__')
