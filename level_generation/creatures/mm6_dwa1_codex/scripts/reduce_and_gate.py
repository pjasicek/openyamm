import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['polish_motion.py','reduce_body.py']:runpy.run_path(str(P/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];picks=[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,2)]
sys.argv=['g4_weights.py','--',str(P.parent/'work/production_body.blend'),'reduced',*picks];runpy.run_path(str(P/'g4_weights.py'),run_name='__main__')
sys.argv=['g5_hand_stretch.py','--',str(P.parent/'work/production_body.blend'),*roles];runpy.run_path(str(P/'g5_hand_stretch.py'),run_name='__main__')
