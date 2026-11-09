import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/measure_rig.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(P/'work/rig_reduced.blend'),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
