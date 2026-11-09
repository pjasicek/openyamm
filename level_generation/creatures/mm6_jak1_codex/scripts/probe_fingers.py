import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.argv=['fit_fingers.py','--','work/rig_v1.blend'];runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
