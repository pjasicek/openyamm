import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['rebake_far_width.py','rebake_tier_checks.py']:runpy.run_path(str(P/name),run_name='__main__')
