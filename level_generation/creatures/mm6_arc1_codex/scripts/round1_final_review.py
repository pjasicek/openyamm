import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['round1_export_gates.py','final_review.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
