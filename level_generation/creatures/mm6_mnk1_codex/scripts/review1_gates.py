import runpy,os,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ['GATE_BLEND']=str(p/'work/animation_finish.blend');runpy.run_path(str(p/'scripts/gates_dense.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(p/'work/animation_finish.blend'),'Standing','Walking','Running','Fidget','Hit','Attack','Cast','Death','Dead'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
