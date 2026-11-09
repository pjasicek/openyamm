import bpy,sys,runpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
sys.argv=['hands','--',str(p/'work/rig_v10.blend'),*roles]
runpy.run_path(str(p/'scripts/g5_hand_stretch.py'),run_name='__main__')
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
pv=np.zeros(len(o.data.vertices),np.int32);o.data.attributes['piece'].data.foreach_get('value',pv);C=np.flatnonzero(pv==9)
report={}
for name in roles:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];world=[];local=[]
 for f in np.arange(0,max(1,a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();X=np.array([m.vertices[int(i)].co[:] for i in C]);ev.to_mesh_clear()
  world.append(X);P=np.array(r.pose.bones['B_Pelvis'].matrix.inverted());local.append(X@P[:3,:3].T+P[:3,3])
 world=np.array(world);local=np.array(local);step=np.linalg.norm(np.diff(local,axis=0),axis=2);jerk=np.linalg.norm(np.diff(local,n=2,axis=0),axis=2)
 report[name]={'floor_min_mm':float(world[:,:,2].min()*1000),'local_step_60fps_mm':float(step.max()*1000),'local_second_difference_60fps_mm':float(jerk.max()*1000),'world_step_60fps_mm':float(np.linalg.norm(np.diff(world,axis=0),axis=2).max()*1000)}
 assert report[name]['floor_min_mm']> -10,(name,report[name])
 if name in ['Standing','Fidget']:
  assert report[name]['local_step_60fps_mm']<2 and report[name]['local_second_difference_60fps_mm']<1,(name,report[name])
 if name=='Walking':assert report[name]['local_step_60fps_mm']<5,(name,report[name])
 print('TEMPORAL',name,report[name],flush=True)
(p/'review/feedback_20261011/temporal_check.json').write_text(json.dumps(report,indent=1))
sys.argv=['final_review','--']
runpy.run_path(str(p/'scripts/final_review.py'),run_name='__main__')
