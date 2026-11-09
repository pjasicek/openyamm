"""Re-run affected motion, hand, contact and head-clearance gates on the revised master."""
from pathlib import Path
import bpy,sys,runpy,json
p=Path(__file__).resolve().parents[1];blend=str(p/'work/rig_v15.blend');scripts=p/'scripts';roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
for script,args in [('g5_hand_stretch.py',roles),('g6_head_clearance.py',roles),('g6_contacts.py',['Standing','Running','Fidget','Death','Dead']),('g6_skirt_poke.py',['Standing','Running','Fidget','Death','Dead'])]:
 sys.argv=[script,'--',blend,*args];runpy.run_path(str(scripts/script),run_name='__main__')
# Full arm edge sweep on new clips, plus retained clips with the new neck geometry.
sys.argv=['g4_weights.py','--',blend,'revision2',*[f'{n}:{f}' for n,frames in [('Standing',[0,30,60]),('Running',range(0,25,2)),('Fidget',range(0,61,5)),('Death',range(0,40,2)),('Attack',[20,28]),('Hit',[7])] for f in frames]]
runpy.run_path(str(scripts/'g4_weights.py'),run_name='__main__')

exec(compile((scripts/'uv_gate.py').read_text().replace('rig_v6.blend','rig_v15.blend'),str(scripts/'uv_gate.py'),'exec'),globals())
