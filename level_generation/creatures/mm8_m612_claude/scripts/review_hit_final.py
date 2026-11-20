import os,runpy
from pathlib import Path
os.environ['GOG_REVIEW_CLIP']='Hit'
runpy.run_path(str(Path(__file__).with_name('final_review.py')),run_name='__main__')
