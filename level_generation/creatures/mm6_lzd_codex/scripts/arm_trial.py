import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/final_arm_polish.py'),run_name='__main__')
sys.argv=['g6','--',str(P/'work/rig_reduced.blend'),'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
