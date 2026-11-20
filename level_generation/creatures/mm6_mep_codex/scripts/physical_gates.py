"""48 Hz palm orientation, actual hand-to-shaft contact and heel/toe measurements."""
import bpy,json,math,numpy as np,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/final_lod0.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;B=r.data.bones
pv=np.array([x.value for x in b.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in b.data.vertices])
hand=B['B_L_Hand'];finger=(B['B_L_Finger2'].head_local-hand.head_local).normalized();normal=(B['Socket_Palm_Left'].head_local-hand.head_local-finger*.042).normalized()
palm_local=hand.matrix_local.to_3x3().inverted()@normal
footsets={};sole_weights={}
for sd,part in [('L',11),('R',10)]:
 mask=pv==part;low=rest[mask,2].min();sole=mask&(rest[:,2]<low+.004);middle=np.median(rest[sole,1]);footsets[sd]=(np.where(sole&(rest[:,1]<=middle))[0],np.where(sole&(rest[:,1]>middle))[0])
# Area-weighted sole direction is invariant to triangulation and vertex redistribution.
for sd,part in [('L',11),('R',10)]:
 w=np.zeros(len(rest))
 for face in b.data.polygons:
  if all(pv[i]==part for i in face.vertices) and face.normal.z<-.8:
   for i in face.vertices:w[i]+=face.area/len(face.vertices)
 assert w.sum()>0
 sole_weights[sd]=w/w.sum()
hand_ids=np.where(pv==3)[0];hand_remap={int(i):j for j,i in enumerate(hand_ids)};hand_faces=[tuple(hand_remap[i] for i in f.vertices) for f in b.data.polygons if all(pv[i]==3 for i in f.vertices)]
report={}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];palms=[];grips=[];feet={s:{'heel_mm':[],'toe_mm':[],'forward_degrees':[]} for s in 'LR'};floor=[];staff_floor=[]
 for f in sorted(set(list(np.arange(0,float(a.frame_range[1])+.00001,30/48))+[float(a.frame_range[1])])):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();floor.append(float(P[pv!=100,2].min()*1000));staff_floor.append(float(P[pv==100,2].min()*1000))
  nh=r.pose.bones['B_L_Hand'].matrix.to_3x3()@palm_local;chest=r.pose.bones['B_Spine2'].matrix.to_3x3()@B['B_Spine2'].matrix_local.to_3x3().inverted();palms.append(float(nh.dot(chest@Vector((-1,0,0)))))
  if a.name not in ['Death','Dead'] or (a.name=='Death' and f<4.5):
   inv=r.pose.bones['Staff'].matrix.inverted();shaft=np.array([inv@Vector(x) for x in P[pv==3]]);near=shaft[np.abs(shaft[:,1])<.055];assert len(near)
   tree=BVHTree.FromPolygons([Vector(x) for x in shaft],hand_faces);distances=[tree.find_nearest(Vector((0,float(y),0)))[3] for y in np.linspace(-.05,.05,101)];grips.append(float((min(distances)-.0109)*1000))
  for sd,(toe,heel) in footsets.items():
   w=sole_weights[sd];center=np.sum(P*w[:,None],axis=0);q=P[:,:2]-center[:2];cov=(q*w[:,None]).T@q;values,vectors=np.linalg.eigh(cov);d=vectors[:,-1];d=d if d[1]<0 else -d;feet[sd]['toe_mm'].append(float(P[toe,2].min()*1000));feet[sd]['heel_mm'].append(float(P[heel,2].min()*1000));feet[sd]['forward_degrees'].append(math.degrees(math.atan2(d[0],-d[1])))
 rest_role=a.name in ['Standing','Fidget'];gait=a.name in ['Standing','Fidget','Walking','Running']
 row={'samples_48hz':len(palms),'free_palm_inward_dot':[min(palms),max(palms)],'grip_surface_gap_mm':[min(grips),max(grips)] if grips else None,'body_lowest_mm':min(floor),'staff_lowest_mm':min(staff_floor),'feet':{sd:{k:[min(v),max(v)] for k,v in vals.items()} for sd,vals in feet.items()}}
 row['palm_pass']=min(palms)>(.85 if gait else 0)
 row['grip_pass']=not grips or (min(grips)>=-2 and max(grips)<=3)
 row['feet_pass']=not rest_role or all(max(abs(x) for x in feet[sd][part])<=10 for sd in 'LR' for part in ['heel_mm','toe_mm'])
 row['gait_heading_pass']=not gait or all(max(abs(x) for x in feet[sd]['forward_degrees'])<=10 for sd in 'LR')
 row['floor_pass']=min(floor)>=-2 and min(staff_floor)>=-2
 report[a.name]=row;print('PHYSICAL',a.name,json.dumps(row),flush=True)
(p/os.environ.get('PHYSICAL_REPORT','review/final/physical_lod0.json')).write_text(json.dumps(report,indent=2))
assert all(all(v[k] for k in ['palm_pass','grip_pass','feet_pass','gait_heading_pass','floor_pass']) for v in report.values()),'Physical gate failed'
