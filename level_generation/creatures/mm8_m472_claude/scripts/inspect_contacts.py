"""All-frame deformation and floor probes; cloth penetration uses only the closed, concealed legs."""
from pathlib import Path
import bpy,json,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_gated.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);cr=np.array([x.value for x in me.attributes['cloth_region'].data])
edges=np.array([tuple(e.vertices) for e in me.edges]);length=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
gn=[g.name for g in body.vertex_groups]
feet=(pv==12)&(co[:,2]<.12);solid=np.isin(pv,[2,3,4,8,9,10,11,12])|((pv==0)&(co[:,2]>1.075)&(abs(co[:,0])<.19))
hand=np.isin(pv,[3,4]);arm=(pv==0)&(cr==0)&(abs(co[:,0])>.14)&(co[:,2]>1.06)
regions={'hands':hand,'arms':arm,'robe':cr==1,'cuffs':np.isin(cr,[2,3]),'hair':cr==4,'tassels':cr==5}
em={n:mask[edges[:,0]]&mask[edges[:,1]]&(length>.0005) for n,mask in regions.items()}
legfaces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==12 for i in f.vertices)]
report={}
for act in bpy.data.actions:
 if act.name not in ['Death','Walking','Running','Standing']:continue
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 r={'stretch':{n:{'max':0.,'p99':0.,'frame':0} for n in regions},'cloth_floor_min_m':1.,'shoe_min_range_m':[1.,-1.],'robe_leg_inside_max':0,'robe_leg_depth_m':0.,'jerk_degrees_per_half_frame':{}}
 last={}
 for f in np.arange(0,act.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  for n in ['B_Head','B_L_Hand','B_R_Hand','B_L_Foot','B_R_Foot']:
   q=rig.pose.bones[n].matrix.to_quaternion().normalized()
   if n in last:r['jerk_degrees_per_half_frame'][n]=max(r['jerk_degrees_per_half_frame'].get(n,0),math.degrees(2*math.acos(min(1.,abs(q.dot(last[n]))))))
   last[n]=q
  if f%1:continue
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pos=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();assert np.isfinite(pos).all()
  ratio=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)/np.maximum(length,1e-6)
  for n,mask in em.items():
   values=ratio[mask];q=r['stretch'][n];q['p99']=max(q['p99'],float(np.quantile(values,.99)))
   if values.max()>q['max']:q['max']=float(values.max());q['frame']=int(f)
  floor_i=int(np.argmin(np.where(cr>0,pos[:,2],1e9)))
  if pos[floor_i,2]<r['cloth_floor_min_m']:r['floor_vertex']={'frame':float(f),'vertex':floor_i,'piece':int(pv[floor_i]),'region':int(cr[floor_i]),'rest':co[floor_i].tolist(),'posed':pos[floor_i].tolist()}
  r['cloth_floor_min_m']=min(r['cloth_floor_min_m'],float(pos[cr>0,2].min()));low=float(pos[feet,2].min());r['shoe_min_range_m']=[min(r['shoe_min_range_m'][0],low),max(r['shoe_min_range_m'][1],low)]
  tree=BVHTree.FromPolygons(pos.tolist(),legfaces)
  inside=0;depth=0
  for i in np.where(cr==1)[0]:
   hit,n,_,dist=tree.find_nearest(Vector(pos[i]))
   if hit is not None and (Vector(pos[i])-hit).dot(n)<-.004:
    direction=Vector((1,.371,.237)).normalized();origin=Vector(pos[i]);crossings=0
    for _ in range(20):
     loc,_,_,_=tree.ray_cast(origin,direction)
     if loc is None:break
     crossings+=1;origin=loc+direction*.00001
    if crossings%2:
     inside+=1;depth=max(depth,dist)
     if dist>r['robe_leg_depth_m']:r['penetrating_vertex']={'frame':float(f),'vertex':int(i),'rest':co[i].tolist(),'posed':pos[i].tolist(),'depth':dist}
  r['robe_leg_inside_max']=max(r['robe_leg_inside_max'],inside);r['robe_leg_depth_m']=max(r['robe_leg_depth_m'],depth)
 report[act.name]=r
 print('DEFORMATION',act.name,json.dumps(r),flush=True)
(p/'work/contacts_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
