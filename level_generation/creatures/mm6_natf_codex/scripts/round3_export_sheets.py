import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['round3_export.py','round3_sheets.py']:runpy.run_path(str(p/n),run_name='__main__')
