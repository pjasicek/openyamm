"""Smuggler cloth and equipment weights; keep Meshy joint weighting on the continuous body surfaces."""
import bpy,sys,os,json
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
def rigid(ids,name):
 W[ids]=0;W[ids,gi[name]]=1
# The beard belongs to the head even where its tip passes the neck.
rigid(np.where((pv==0)&((co[:,2]>1.42)|(co[:,1]<-.07)))[0],'B_Head')
rigid(np.where(np.isin(pv,[19,20,23,24]))[0],'B_Head')
rigid(np.where(np.isin(pv,[8,9,18,51,53,54,56,58,60,61,63,64,66,68,69]))[0],'B_Pelvis')
rigid(np.where(np.isin(pv,[10,15,21,22]))[0],'B_R_Thigh')
shirt=np.where(pv==1)[0];kd=KDTree(len(shirt))
for i in shirt:kd.insert(co[i],int(i))
kd.balance()
arm=[i for n,i in gi.items() if any(k in n for k in ('UpperArm','Forearm','Hand','Finger'))]
for part in [7,11,13,16,17,32]:
 ids=np.where(pv==part)[0]
 for i in ids:
  hits=kd.find_n(co[i],4);weights=np.array([1/max(h[2],1e-4) for h in hits]);W[i]=(weights[:,None]*W[[h[1] for h in hits]]).sum(0)/weights.sum();W[i,arm]=0;W[i]/=W[i].sum()
for side,part in [('L',12),('R',14)]:
 ids=np.where(pv==part)[0]
 for i in ids:
  W[i,gi[f'B_{side}_Forearm']]+=W[i,gi[f'B_{side}_Hand']];W[i,gi[f'B_{side}_Hand']]=0
 sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{side}_Clavicle'].head_local);d=(sh-cl)/np.linalg.norm(sh-cl)
 for i in shirt:
  m=(co[i]-sh)@d
  if m<0:
   ua,cv=gi[f'B_{side}_UpperArm'],gi[f'B_{side}_Clavicle'];dw=W[i,ua]*(1-max(0,1+m/.07));W[i,ua]-=dw;W[i,cv]+=dw
# Meshy's armpit weights jumped by 13% across a 4 mm edge; diffuse that gradient on the tunic only.
nb=[[] for _ in co]
for edge in me.edges:
 a,b=edge.vertices
 if pv[a]==1 and pv[b]==1:nb[a].append(b);nb[b].append(a)
for _ in range(4):
 old=W.copy()
 for i in shirt:
  if nb[i]:W[i]=.4*old[i]+.6*old[nb[i]].mean(0)
# The distal palm and thumb root cannot inherit forearm roll.
for side,part in [('L',3),('R',4)]:
 wr=np.array(rig.data.bones[f'B_{side}_Hand'].head_local);kn=np.array(rig.data.bones[f'B_{side}_Finger2'].head_local);d=(kn-wr)/np.linalg.norm(kn-wr)
 for i in np.where(pv==part)[0]:
  u=float(np.clip(((co[i]-wr)@d-.01)/.025,0,1))
  for name in [f'B_{side}_Forearm',f'B_{side}_ForearmTwist']:
   dw=W[i,gi[name]]*u;W[i,gi[name]]-=dw;W[i,gi[f'B_{side}_Hand']]+=dw
assert np.isfinite(W).all() and np.min(W.sum(1))>.99
W/=W.sum(1,keepdims=True)
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for name in names:body.vertex_groups.new(name=name)
for i in range(len(co)):
 for j in np.where(W[i]>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(W[i,j]),'REPLACE')
print('RULE Smuggler: head/beard, belt, right thigh sheath, bandolier, pouches, cuffs, shoulder fade')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
