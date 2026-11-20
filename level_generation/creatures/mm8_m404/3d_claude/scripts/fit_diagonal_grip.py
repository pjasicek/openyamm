import os,runpy
from pathlib import Path
p=Path(__file__).resolve().parent
os.environ['GRIP_TILT']='20'
runpy.run_path(str(p/'grip_refine.py'),run_name='__main__')
runpy.run_path(str(p/'check_fit_pipeline.py'),run_name='__main__')
runpy.run_path(str(p/'grip_surface.py'),run_name='__main__')
