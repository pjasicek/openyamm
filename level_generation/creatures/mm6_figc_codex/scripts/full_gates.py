import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];src=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else str(P/'work/equipped.blend')
bpy.ops.wm.open_mainfile(filepath=src);rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
names=[g.name for g in body.vertex_groups];rest=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([d.value for d in me.attributes['piece'].data]);E=np.array([tuple(e.vertices) for e in me.edges]);RL=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
Wt=np.zeros((len(rest),len(names)))
for v in me.vertices:
 for g in v.groups:Wt[v.index,g.group]=g.weight
weight=lambda keys:Wt[:,[i for i,n in enumerate(names) if any(k in n for k in keys)]].sum(1)
arm=weight(['UpperArm','Forearm'])>.3;hand=weight(['Hand','Finger'])>.3
AE=arm[E].all(1);HE=hand[E].all(1);skirt=(pv==0)&(rest[:,2]>.6)&(rest[:,2]<1.03);SE=skirt[E].all(1)
faces=[tuple(p.vertices) for p in me.polygons];sets={}
for side,sign in [('L',1),('R',-1)]:
 own=np.array([sum(g.weight for g in v.groups if names[g.group].startswith('B_'+side+'_') and any(k in names[g.group] for k in ['Clavicle','UpperArm','Forearm','Hand','Finger']))>.2 for v in me.vertices])
 sample=np.where((weight([f'B_{side}_Forearm',f'B_{side}_Hand',f'B_{side}_Finger'])>.5))[0]
 sets[side]=(sample,[f for f in faces if not own[list(f)].any()])
head=np.where(np.isin(pv,[3,10,11,15,16])|((pv==0)&(rest[:,2]>1.48)))[0]
shoulders=[f for f in faces if np.isin(pv[list(f)],[7,8]).all()]
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return p
def inside(p,tree):
 # Nearest-face signs alone misclassify points outside the open armpit/hem; require three-ray majority.
 votes=0
 for d in [Vector((.932,.217,.291)).normalized(),Vector((-.313,.901,.299)).normalized(),Vector((.243,-.372,.896)).normalized()]:
  origin=Vector(p)+d*1e-6;hits=0
  for _ in range(40):
   loc,n,fi,dist=tree.ray_cast(origin,d,5)
   if loc is None:break
   hits+=1;origin=loc+d*1e-5
  votes+=hits%2
 return votes>=2

def depth(points,tree):
 worst=(0,None)
 for i,p in enumerate(points):
  loc,n,fi,d=tree.find_nearest(Vector(p),.05)
  if loc is not None and d>worst[0] and (Vector(p)-loc).dot(n)<-.707*d and inside(p,tree):worst=(d,fi)
 return worst
report={}
roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
for name in roles:
 if name not in bpy.data.actions:continue
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 row={'arm_p99':0,'arm_max':0,'finger_max':0,'skirt_p99':0,'skirt_max':0,'head_mm':0,'L_contact_mm':0,'R_contact_mm':0,'Axe_mm':0,'Shield_mm':0,'minimum_z':1e9,'pelvis_min':1e9,'pelvis_max':-1e9,'trunk_lean_max':0,'frames':0,'worst':{}}
 for f in np.arange(0,float(act.frame_range[1])+.001,.625):
  scene.frame_set(int(f),subframe=float(f%1));co=coords(body);C=np.array(co);ratio=np.linalg.norm(C[E[:,0]]-C[E[:,1]],axis=1)/np.maximum(RL,1e-6)
  vals={'arm_p99':np.percentile(ratio[AE],99),'arm_max':ratio[AE].max(),'finger_max':ratio[HE].max(),'skirt_p99':np.percentile(ratio[SE],99),'skirt_max':ratio[SE].max()}
  for side,(samples,fs) in sets.items():
   tree=BVHTree.FromPolygons(co,fs);d,fi=depth([co[i] for i in samples],tree);vals[side+'_contact_mm']=d*1000
  tree=BVHTree.FromPolygons(co,shoulders);vals['head_mm']=depth([co[i] for i in head],tree)[0]*1000
  for prop,side in [('Axe','R'),('Shield','L')]:
   if prop not in bpy.data.objects:continue
   obj=bpy.data.objects[prop];pc=coords(obj);exclude=weight([f'B_{side}_Hand',f'B_{side}_Finger'])>.3
   fs=[fc for fc in faces if not exclude[list(fc)].any()];tree=BVHTree.FromPolygons(co,fs);vals[prop+'_mm']=depth(pc,tree)[0]*1000
  for k,v in vals.items():
   if v>row[k]:row[k]=float(v);row['worst'][k]=float(f)
  row['minimum_z']=min(row['minimum_z'],float(C[:,2].min()));pel=rig.pose.bones['B_Pelvis'].head;neck=rig.pose.bones['B_Neck'].head;vec=neck-pel;lean=math.degrees(vec.angle(Vector((0,0,1))))
  row['pelvis_min']=min(row['pelvis_min'],float(pel.z));row['pelvis_max']=max(row['pelvis_max'],float(pel.z));row['trunk_lean_max']=max(row['trunk_lean_max'],lean);row['frames']+=1
 report[name]=row;print('FULLGATE',name,json.dumps(row),flush=True)
(P/'work/full_gates.json').write_text(json.dumps(report,indent=2))
