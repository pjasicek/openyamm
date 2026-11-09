from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for name in ['finish_motion.py','export_review.py']:
 s=p/'scripts'/name;sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
