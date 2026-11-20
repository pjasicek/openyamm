from pathlib import Path
import sys,os,runpy
p=Path(__file__).resolve().parents[1]
os.environ['GRIP_RENDER']=str(p/'review/grip')
sys.argv=['grip_solve.py','--',str(p/'work/pilot.blend'),'Standing','0']
runpy.run_path(str(p/'scripts/grip_solve.py'),run_name='__main__')
