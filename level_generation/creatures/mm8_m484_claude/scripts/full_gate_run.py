import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['CHECK_BLEND']='work/pilots_cloth.blend';os.environ['CHECK_PREFIX']='full';os.environ['STEP']='.5'
for n in ['motion_gates.py','check_contacts.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
for n in ['jerk_probe.py','stride.py']:
 sys.argv=[n,'--',str(P/'work/pilots_cloth.blend'),*(roles if n=='jerk_probe.py' else ['Walking','Running'])];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
sys.argv=['jerk_probe.py','--',str(P/'work/rig_motion.blend'),*roles];runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
