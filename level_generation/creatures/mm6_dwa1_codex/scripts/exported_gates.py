import bpy,sys,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
for n in ['import_final.py','contact_final.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];picks=[f'{n}:{f}'for n in roles for f in np.arange(0,float(bpy.data.actions[n].frame_range[1])+1e-5,bpy.context.scene.render.fps/48)]
sys.argv=['g4_weights.py','--',str(P/'work/export_reimport.blend'),'exported',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
sys.argv=['g5_hand_stretch.py','--',str(P/'work/export_reimport.blend'),*roles];runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
sys.argv=['glb_hand_closeups.py','--',str(P/'review/viewer/mm6_dwa1_a.glb'),str(P/'review/final_hand'),'Standing:0','Attack:0.71875'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
