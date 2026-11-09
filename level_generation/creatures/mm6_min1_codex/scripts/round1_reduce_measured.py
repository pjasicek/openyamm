import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_protect_contacts.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),run_name='__main__')
