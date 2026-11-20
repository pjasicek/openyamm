import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
sys.argv=['hands','--',str(p/'work/rig_v10.blend'),*roles]
runpy.run_path(str(p/'scripts/g5_hand_stretch.py'),run_name='__main__')
sys.argv=['render','--']
runpy.run_path(str(p/'scripts/feedback_preview.py'),run_name='__main__')
