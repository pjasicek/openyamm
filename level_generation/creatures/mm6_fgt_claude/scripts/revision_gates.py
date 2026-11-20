from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
for name in ('g6_contacts.py','g6_head_clearance.py','g4_skirt.py','g6_skirt_poke.py','g5_hand_stretch.py'):
 sys.argv=[str(p/'scripts'/name),'--',str(p/'work/rig_revision1.blend'),*roles]
 runpy.run_path(sys.argv[0],run_name='__main__')
sys.argv=[str(p/'scripts/g4_weights.py'),'--',str(p/'work/rig_revision1.blend'),'native','Standing:0','Walking:6','Attack:16','Attack:19','Attack:21','Attack:24','Hit:6','Death:20']
runpy.run_path(sys.argv[0],run_name='__main__')
