import os, runpy
from pathlib import Path
os.environ.update(REA_INFLUENCES='4', REA_RATIOS='0.94')
runpy.run_path(str(Path(__file__).with_name('reduce_ladder.py')), run_name='__main__')
