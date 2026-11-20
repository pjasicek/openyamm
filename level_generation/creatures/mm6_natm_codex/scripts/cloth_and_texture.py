import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for s in ['cloth_fit.py','contact_audit.py','texture_layout.py']:
 sys.argv=[s];runpy.run_path(str(P/'scripts'/s),run_name='__main__')
