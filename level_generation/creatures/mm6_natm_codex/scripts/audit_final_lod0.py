import bpy,sys,json,math,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
blend=P/'work/final_lod0.blend';out=P/'review/final_lod0';out.mkdir(exist_ok=True)
def invoke(script):
 code=(P/f'scripts/{script}.py').read_text().replace("work/contact_master.blend","work/final_lod0.blend").replace("work/material_master.blend","work/final_lod0.blend").replace("'review/","'review/final_lod0/")
 exec(compile(code,str(P/f'scripts/{script}.py'),'exec'),{'__name__':'__main__','__file__':str(P/f'scripts/{script}.py')})
bpy.ops.wm.open_mainfile(filepath=str(blend));r=bpy.data.objects['Rig'];sc=bpy.context.scene;report={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rots={}
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f)
  for n in [f'B_{sd}_{part}'for sd in 'LR'for part in ['UpperArm','Forearm','Hand']]:
   rots.setdefault(n,[]).append(r.pose.bones[n].matrix.to_quaternion())
 row={}
 for n,qs in rots.items():
  vel=[]
  for x,y in zip(qs,qs[1:]):
   q=y@x.inverted()
   if q.w<0:q=-q
   axis,angle=q.to_axis_angle();vel.append(np.array(axis)*angle*48)
  vv=np.array(vel);row[n]={'step_deg':float(np.linalg.norm(vv,axis=1).max()*180/math.pi/48),'acceleration_deg_s2':float(np.linalg.norm(np.diff(vv,axis=0),axis=1).max(initial=0)*48*180/math.pi)}
 report[a.name]=row;print('ACCEL',a.name,row,flush=True)
(out/'acceleration.json').write_text(json.dumps(report,indent=2))
invoke('motion_pose_audit');invoke('motion_steps');invoke('contact_audit')
for name in ['g5_hand_stretch','g6_contacts','g6_head_clearance']:
 sys.argv=[name,'--',str(blend),*['Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death','Dead']];runpy.run_path(str(P/f'scripts/{name}.py'),run_name='__main__')
picks=[a.name+':'+str(f)for a in bpy.data.actions for f in range(int(a.frame_range[1])+1)]
sys.argv=['g4','--',str(blend),'final_lod0',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
