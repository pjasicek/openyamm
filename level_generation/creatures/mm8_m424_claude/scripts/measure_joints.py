import sys, runpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.argv = ['fit_joints.py', '--', str(P/'work/step1.blend'), 'Body']
runpy.run_path(str(P/'scripts/fit_joints.py'), run_name='__main__')
