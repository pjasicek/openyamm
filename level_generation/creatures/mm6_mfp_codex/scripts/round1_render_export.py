import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['export_reimport','final_sheets']:runpy.run_path(str(p/(n+'.py')),run_name='__main__')
