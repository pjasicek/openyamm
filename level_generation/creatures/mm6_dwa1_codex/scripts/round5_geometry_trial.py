import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for s in ['round5_geometry.py','round5_candidate.py']:runpy.run_path(str(P/'scripts'/s),run_name='__main__')
