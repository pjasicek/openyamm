import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));blend=P/'work/material_master.blend'
runpy.run_path(str(P/'scripts/motion_pose_audit.py'),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death','Dead']
for name in ['g5_hand_stretch','g6_contacts','g6_head_clearance']:
 sys.argv=[name,'--',str(blend),*roles];runpy.run_path(str(P/f'scripts/{name}.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/motion_steps.py'),run_name='__main__')
picks=[]
for a in bpy.data.actions:
 for f in range(int(a.frame_range[1])+1):picks.append(a.name+':'+str(f))
sys.argv=['g4','--',str(blend),'all48',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
