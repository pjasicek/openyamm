import os,runpy
from pathlib import Path
os.environ.update(REA_CAND='Cand_94',REA_INFLUENCES='4',REA_NODE='M440')
runpy.run_path(str(Path(__file__).with_name('export_cand.py')),run_name='__main__')
