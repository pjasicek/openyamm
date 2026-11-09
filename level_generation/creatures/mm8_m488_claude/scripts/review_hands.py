from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for name in ('finish_hands.py','hand_review.py'):
 path=p/'scripts'/name;sys.argv=[str(path),'--'];runpy.run_path(str(path),run_name='__main__')
