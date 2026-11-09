import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['fit_equipment.py','smooth_shoulders.py','mounted_wrist.py','prop_contacts.py']:runpy.run_path(str(p/f),run_name='__main__')
