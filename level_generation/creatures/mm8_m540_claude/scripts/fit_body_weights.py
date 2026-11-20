"""Fit ownership of the Mage's cloth and rigid fittings before pose review."""
from pathlib import Path
import bpy,numpy as np,json,sys,runpy,os
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
s=p/'scripts/twist_bones.py';sys.argv=[str(s),'--',str(p/'work/rig_fingers.blend'),str(p/'work/rig_twist.blend')]
os.environ['FA_RAMP']='0.15,0.85'
runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(names)));gi={n:i for i,n in enumerate(names)}
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
# Upper-arm skin fades medially to its clavicle; neck/head cannot inherit arm motion.
for sd in 'LR':
 sh=np.array(rig.data.bones[f'B_{sd}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{sd}_Clavicle'].head_local);axis=sh-cl;axis/=np.linalg.norm(axis)
 keep=np.clip(1+(co-sh)@axis/.07,0,1)
 for n in [f'B_{sd}_UpperArm',f'B_{sd}_UpperArmTwist']:
  moved=W[:,gi[n]]*(1-keep)*(pv==0);W[:,gi[n]]-=moved;W[:,gi[f'B_{sd}_Clavicle']]+=moved
head=(pv==0)&(co[:,2]>1.37)
W[head]=0;W[head,gi['B_Head']]=1
# Keep the shorts' waist attached to the pelvis above the thigh pivots.
for i in np.where(pv==2)[0]:
 t=float(np.clip((co[i,2]-.75)/.10,0,1));W[i]*=1-t;W[i,gi['B_Pelvis']]+=t
# Garment torso, belt and high collar follow the trunk; the flared collar stays off the head.
spines=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];zs=np.array([rig.data.bones[n].head_local.z for n in spines])
# Core torso skin was following clavicle/arm and thigh estimates; retain those only at the limb transitions.
core=(pv==0)&(co[:,2]>.90)&(co[:,2]<1.29)&(abs(co[:,0])<.26)
for i in np.where(core)[0]:
 z=co[i,2];j=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[j])/(zs[j+1]-zs[j]),0,1))
 amount=float(np.clip((.26-abs(co[i,0]))/.10,0,1)*np.clip((1.29-z)/.06,0,1)*np.clip((z-.90)/.05,0,1))
 W[i]*=1-amount;W[i,gi[spines[j]]]+=amount*(1-t);W[i,gi[spines[j+1]]]+=amount*t
print('TORSO_WEIGHT_MATCH',int(core.sum()))

for i in np.where(pv==1)[0]:
 z=co[i,2];j=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[j])/(zs[j+1]-zs[j]),0,1));W[i]=0;W[i,gi[spines[j]]]=1-t;W[i,gi[spines[j+1]]]=t
# The fitted vest must follow the skin beneath it through the shoulder/chest motion.
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
me.calc_loop_triangles()
tris=[t for t in me.loop_triangles if all(pv[i]==0 for i in t.vertices) and all(.90<co[i,2]<1.39 for i in t.vertices)]
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in tris],all_triangles=True)
fit_count=0
for i in np.where((pv==1)&(co[:,2]>.94)&(co[:,2]<1.34))[0]:
 loc,normal,ti,distance=tree.find_nearest(Vector(co[i]))
 if distance>.045:continue
 t=tris[ti];abc=[me.vertices[j].co for j in t.vertices]
 bc=barycentric_transform(loc,*abc,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 weights=np.maximum(np.array(bc),0);weights/=weights.sum()
 W[i]=sum((W[j]*w for j,w in zip(t.vertices,weights)),np.zeros(W.shape[1]));fit_count+=1
print('VEST_SKIN_WEIGHT_MATCH',fit_count)
for part in [5,6,7,8,11,12,*range(13,25),25,26,27,9,10]:
 ids=np.where(pv==part)[0];c=co[ids].mean(0)
 if part==5:n='B_Pelvis'
 elif part in [6,7,8,11,12]:n='B_Head'
 elif 13<=part<=24:n=f"B_{'L' if c[0]>0 else 'R'}_UpperArm"
 elif part in [9,10]:n=f"B_{'L' if c[0]>0 else 'R'}_Calf"
 else:n=min(spines,key=lambda n:abs(rig.data.bones[n].head_local.z-c[2]))
 W[ids]=0;W[ids,gi[n]]=1
assert np.isfinite(W).all() and np.min(W.sum(1))>.99
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i in range(len(co)):
 for j in np.where(W[i]>.0001)[0]:body.vertex_groups[j].add([i],float(W[i,j]/W[i].sum()),'REPLACE')
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for k,(z,y,zend,yend) in enumerate([(1.26,.15,.90,.20),(.90,.20,.57,.23),(.57,.23,.24,.27)]):
 b=rig.data.edit_bones.new(f'Cape{k}');b.head=(0,y,z);b.tail=(0,yend,zend);b.parent=rig.data.edit_bones['B_Spine2' if k==0 else f'Cape{k-1}']
b=rig.data.edit_bones.new('LoinFront');b.head=(0,-.21,.91);b.tail=(0,-.22,.64);b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
for n in ['Cape0','Cape1','Cape2','LoinFront']:body.vertex_groups.new(name=n)
# The cape is a separate connected cloth component below the shoulder bridge; shorts share the same piece id.
eligible=(pv==1)&(co[:,2]<1.16);seed=int(np.argmin(np.where(eligible,co[:,2],10)))
adj={int(i):[] for i in np.where(eligible)[0]}
for edge in me.edges:
 a,b=edge.vertices
 if eligible[a] and eligible[b]:adj[a].append(b);adj[b].append(a)
seen={seed};todo=[seed]
while todo:
 for j in adj[todo.pop()]:
  if j not in seen:seen.add(j);todo.append(j)
cape=np.zeros(len(co),bool);cape[list(seen)]=True
assert 300<cape.sum()<450,(cape.sum(),'cape connectivity changed')
front=(pv==1)&(~cape)&(co[:,1]<-.17)&(abs(co[:,0])<.14)&(co[:,2]<.90)
# The shorts follow the actual leg skin instead of being mistaken for either hanging cloth panel.
leg_tris=[t for t in me.loop_triangles if all(pv[i]==2 for i in t.vertices)]
leg_tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in leg_tris],all_triangles=True)
short_ids=np.where((pv==1)&(~cape)&(~front)&(co[:,2]<.94))[0]
for i in short_ids:
 loc,normal,ti,distance=leg_tree.find_nearest(Vector(co[i]));tri=leg_tris[ti]
 abc=[me.vertices[j].co for j in tri.vertices]
 bc=barycentric_transform(loc,*abc,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 weights=np.maximum(np.array(bc),0);weights/=weights.sum()
 row=sum((W[j]*w for j,w in zip(tri.vertices,weights)),np.zeros(W.shape[1]))
 for group in body.vertex_groups:group.remove([int(i)])
 for j in np.where(row>.0001)[0]:body.vertex_groups[j].add([int(i)],float(row[j]/row.sum()),'REPLACE')
print('SHORTS_SKIN_WEIGHT_MATCH',len(short_ids))
# The generated panel root started inside the shorts; move only cloth toward the nearest outer skin surface.
skin_tris=[t for t in me.loop_triangles if all(pv[i] in (0,2,3,4) for i in t.vertices)]
cloth_tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in skin_tris],all_triangles=True)
repairs=[]
for i in np.where(front|cape)[0]:
 v=me.vertices[int(i)];loc,normal,ti,distance=cloth_tree.find_nearest(v.co,.06)
 if loc is None or (front[i] and normal.y>0) or (cape[i] and normal.y<.4):continue
 signed=(v.co-loc).dot(normal)
 if signed<.012:
  delta=.012-signed;assert delta<.075
  v.co+=normal*delta;repairs.append(delta)
print('CLOTH_REST_CLEARANCE',len(repairs),max(repairs,default=0))
# Native back views taper the cape to a central calf-level point, unlike the generated broad lower hem.
for i in np.where(cape)[0]:
 v=me.vertices[int(i)];z=co[i,2];x=co[i,0]
 v.co.x*=.25+.75*float(np.clip((z-.24)/.80,0,1))
 v.co.z+=.20*(abs(x)/.40)**2*float(np.clip((.90-z)/.65,0,1))
for i in np.where((pv==1)&(co[:,1]>.11)&(co[:,2]>1.0)&(co[:,2]<1.35))[0]:
 t=float(np.clip((co[i,2]-1.0)/.10,0,1)*np.clip((1.35-co[i,2])/.20,0,1))
 me.vertices[int(i)].co.x*=1-.06*t

# Leave a centimetre of cloth ease across the moving shoulder blades; taper into the collar and waist.
for i in np.where((pv==1)&(co[:,1]>.11)&(co[:,2]>.90)&(co[:,2]<1.35))[0]:
 ease=float(np.clip((co[i,2]-.90)/.10,0,1)*np.clip((1.35-co[i,2])/.15,0,1))
 me.vertices[int(i)].co.y+=.012*ease


for i in np.where(cape|front)[0]:
 for g in body.vertex_groups:g.remove([int(i)])
 if front[i]:
  t=float(np.clip((.92-co[i,2])/.10,0,1));body.vertex_groups['B_Pelvis'].add([int(i)],1-t,'REPLACE');body.vertex_groups['LoinFront'].add([int(i)],t,'REPLACE')
 else:
  z=co[i,2];centres=[1.16,.98,.65,.35];bones=['B_Spine2','Cape0','Cape1','Cape2'];j=int(np.clip(np.searchsorted(-np.array(centres),-z)-1,0,2));t=float(np.clip((centres[j]-z)/(centres[j]-centres[j+1]),0,1))
  follow=float(np.clip((z-.88)/.22,0,1))
  # Cape attachment follows the trunk, never a nearby moving upper arm.
  row=W[i].copy();arm_ids=[k for k,name in enumerate(names) if any(t in name for t in ('Clavicle','UpperArm','Forearm','Hand','Finger'))]
  moved=row[arm_ids].sum();row[arm_ids]=0;row[gi['B_Spine1']]+=moved
  for k in np.where(row>.0001)[0]:body.vertex_groups[k].add([int(i)],float(row[k]*follow),'REPLACE')
  body.vertex_groups[bones[j]].add([int(i)],(1-t)*(1-follow),'ADD');body.vertex_groups[bones[j+1]].add([int(i)],t*(1-follow),'ADD')
for name,mask in [('cape',cape),('loin',front)]:
 a=me.attributes.new(name,'INT','POINT');a.data.foreach_set('value',mask.astype(np.int32));assert mask.sum()>30
print('GARMENT',int(cape.sum()),int(front.sum()),'vertices; bones',len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_body.blend'))
