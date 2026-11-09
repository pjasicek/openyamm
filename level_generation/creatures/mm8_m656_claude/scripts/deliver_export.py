import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['export_final_lods.py','final_physics.py']:
 runpy.run_path(str(P/n),run_name='__main__')
