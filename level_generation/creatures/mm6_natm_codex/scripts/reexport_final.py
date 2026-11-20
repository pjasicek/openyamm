import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['contact_finish','reload_maps','quick_export']:runpy.run_path(str(p/(name+'.py')),run_name='__main__')
