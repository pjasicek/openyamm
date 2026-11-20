import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['round1_weights.py','round1_fit.py','round1_contacts.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
