from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
for n in ['export_pilot.py','run_pilot_gates.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
