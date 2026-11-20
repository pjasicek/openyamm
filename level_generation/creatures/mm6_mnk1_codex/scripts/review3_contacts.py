import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['g6_contacts.py','--',str(p/'work/animation_finish.blend'),'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
