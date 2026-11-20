import os,runpy
from pathlib import Path
os.environ['ROUND2_ROLES']='Death'
runpy.run_path(str(Path(__file__).resolve().with_name('animate_staff.py')),run_name='__main__')
