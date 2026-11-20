import runpy,os,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.environ['SKIP_PILOT_RENDERS']='1'
for n in ['finish_pilot.py','geometry_finish.py','texture_return.py','apply_materials.py','cloth_surface_gate.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
sys.argv=['g6','--',str(p/'work/textured.blend'),'Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
