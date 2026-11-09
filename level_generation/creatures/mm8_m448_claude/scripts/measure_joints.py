from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['fit_joints','--',str(p/'work/step1.blend'),'Body']
runpy.run_path(str(p/'scripts/fit_joints.py'),run_name='__main__')
