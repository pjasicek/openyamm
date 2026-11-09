import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('verify_r6.py')),run_name='__main__')
