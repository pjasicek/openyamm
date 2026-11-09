import bpy,sys,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data
co=np.array([tuple(v.co) for v in me.vertices]);nv=len(co);pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in b.vertex_groups];ix={n:i for i,n in enumerate(names)};W=np.zeros((nv,len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
J=lambda n:np.array(r.data.bones[n].head_local)
def assign(ids,values):
 W[ids]=0
 for n,w in values.items():W[ids,ix[n]]=w
# Skin ends inside the cuff. The visible hand belongs wholly to its own hand chain.
for sd,part in [('L',2),('R',3)]:
 ids=np.where(pv==part)[0];wr=J(f'B_{sd}_Hand');el=J(f'B_{sd}_Forearm');axis=wr-el;axis/=np.linalg.norm(axis)
 a=np.clip(((co[ids]-wr)@axis+.035)/.055,0,1);a=a*a*(3-2*a)
 assign(ids,{f'B_{sd}_Hand':a,f'B_{sd}_Forearm':1-a})
for sd,part in [('L',8),('R',7)]:assign(np.where(pv==part)[0],{f'B_{sd}_Foot':1})
assign(np.where(np.isin(pv,[1,9,10,12]))[0],{'B_Pelvis':.75,'B_Spine':.25})
for part in [4,5,6]:
 ids=np.where(pv==part)[0];h=np.clip((co[ids,2]-1.37)/.105,0,1);h=h*h*(3-2*h)
 if part==5:h*=0
 assign(ids,{'B_Head':h,'B_Spine2':1-h})
ids=np.where(pv==0)[0]
# Sleeve geometry, not the generated anatomical labels, decides arm ownership.
for i in ids:
 z=co[i,2];side='L' if co[i,0]>-.006 else 'R';sh=J(f'B_{side}_UpperArm');el=J(f'B_{side}_Forearm')
 a=float(np.clip((abs(co[i,0]+.006)-.115)/.115,0,1));a=a*a*(3-2*a)
 t=float(np.clip((((co[i]-sh)@(el-sh))/np.dot(el-sh,el-sh)-.68)/.62,0,1));t=t*t*(3-2*t)
 W[i]=0;W[i,ix[f'B_{side}_UpperArm']]=a*(1-t);W[i,ix[f'B_{side}_Forearm']]=a*t
 q=float(np.clip((z-1.10)/.20,0,1));W[i,ix['B_Spine']]=(1-a)*(1-q);W[i,ix['B_Spine2']]=(1-a)*q
# Diffuse the sleeve/torso transition without pulling a hard arm cutoff through the armpit.
nb=[[] for _ in range(nv)]
for e in me.edges:
 a,c=e.vertices
 if pv[a]==pv[c]==0:nb[a].append(c);nb[c].append(a)
for _ in range(18):
 nxt=W.copy()
 for i in ids:
  if nb[i]:nxt[i]=.6*W[i]+.4*W[nb[i]].mean(0)
 W=nxt
# The belt and both overlapping waist shells must share the same blend.
for i in ids:
 a=float(np.clip((1.14-co[i,2])/.10,0,1))*float(np.clip((.235-abs(co[i,0]+.006))/.065,0,1));a=a*a*(3-2*a)
 W[i]*=1-a;W[i,ix['B_Pelvis']]+=a*.75;W[i,ix['B_Spine']]+=a*.25
assert (W.sum(1)>.99).all()
for g in b.vertex_groups:g.remove(list(range(nv)))
for i in range(nv):
 for k in np.where(W[i]>1e-5)[0]:b.vertex_groups[k].add([i],float(W[i,k]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_weights.blend'))
