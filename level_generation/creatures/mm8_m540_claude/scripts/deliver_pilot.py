from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['fit_pilot_cloth.py','pilot_contacts.py','export_pilot.py']:runpy.run_path(str(p/name),run_name='__main__')
