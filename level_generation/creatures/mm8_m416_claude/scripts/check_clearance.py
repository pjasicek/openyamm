from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['refine_clearance.py','all_deformation.py','surface_checks.py']:runpy.run_path(str(p/n),run_name='__main__')
