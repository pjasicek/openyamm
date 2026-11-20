import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ('pilot_motion.py','pilot_review.py'):
    sys.argv=[n,'--'];runpy.run_path(str(P/n),run_name='__main__')
