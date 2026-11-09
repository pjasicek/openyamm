import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
for n in ['polish_cloth.py','limit_cloth_strain.py','build_sword.py','export_review.py','render_strain.py']:
 sys.argv=[n];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
sys.argv=['g5','--',str(p/'work/rig_v8.blend'),'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];runpy.run_path(str(p/'scripts/g5_hand_stretch.py'),run_name='__main__')
