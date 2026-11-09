import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['grip_solve.py','--',str(p/'work/retarget_raw.blend'),'Attack','0']
runpy.run_path(str(p/'scripts/grip_solve.py'),run_name='__main__')
