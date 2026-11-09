import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('cloth_clearance.py','final_cloth_contacts.py','export_uploads.py'):runpy.run_path(str(p/n),run_name='__main__')
