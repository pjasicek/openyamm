import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['weight_probe.py','contact_review.py']:runpy.run_path(str(P/n),run_name='__main__')
