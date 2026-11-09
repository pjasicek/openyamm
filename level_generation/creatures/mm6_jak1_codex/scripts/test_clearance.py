import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['animate_staff.py','refine_deformation.py']:
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
for n in ['g6_contacts.py','g6_skirt_poke.py']:
 sys.argv=[n,'--',str(P/'work/animated_master.blend'),'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')

runpy.run_path(str(P/'scripts/boundary_audit.py'),run_name='__main__')
