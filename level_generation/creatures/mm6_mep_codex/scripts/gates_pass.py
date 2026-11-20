import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ['GATE_BLEND']='work/geometry_final.blend';runpy.run_path(str(p/'scripts/dense_gates.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(p/'work/geometry_final.blend'),'Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
