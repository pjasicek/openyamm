from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['animate_dragon.py','check_wing_contacts.py']:
 runpy.run_path(str(p/name),run_name='__main__')
