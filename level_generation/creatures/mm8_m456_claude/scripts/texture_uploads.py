from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['close_armour_gaps.py','export_uploads.py']:runpy.run_path(str(p/n),run_name='__main__')
