import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['fit_joints.py','--',str(p/'work/step1.blend'),'Body']
runpy.run_path(str(p/'scripts/fit_joints.py'),run_name='__main__')
