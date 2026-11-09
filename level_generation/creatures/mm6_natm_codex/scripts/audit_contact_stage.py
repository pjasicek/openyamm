import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['cloth_floor.py','fix_prop_contacts.py','spear_clearance.py','contact_audit.py','material_review.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
