import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ['smooth_palms.py','export_runtime.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(p/'export/mm6_mnk1.blend'),'Death']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
