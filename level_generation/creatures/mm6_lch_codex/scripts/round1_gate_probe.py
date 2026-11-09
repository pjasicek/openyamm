import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/round1_anatomy_probe.py'),run_name='__main__')
for step in [7,6]:
 rel=f'work/round1/qem_micro/step_{step:02}.blend'
 os.environ['LCH_GATE_BLEND']=rel;os.environ['LCH_GATE_REPORT']=f'review/triangle_reduction/probe_{step}_rig.json';os.environ['LCH_SKIP_GATE_EXPORT']='1'
 runpy.run_path(str(P/'scripts/measure_rig.py'),run_name='__main__')
 os.environ['LCH_CONTACT_REPORT']=f'review/triangle_reduction/probe_{step}_contacts.json'
 sys.argv=['g6_contacts.py','--',str(P/rel),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
 runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
