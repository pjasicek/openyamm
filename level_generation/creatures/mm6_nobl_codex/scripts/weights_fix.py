"""Swordsman shell weights: surface first, rigid armour and trim, jaw free of the shoulders."""
import bpy,sys,os,numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);nv=len(co)
pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
W=np.zeros((nv,len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
assert np.all(W.sum(1)>0),'Unweighted input vertices'
W/=W.sum(1,keepdims=True)
J=lambda n:np.array(rig.data.bones[n].head_local)
def rigid(ids,name):
 W[ids]=0;W[ids,gi[name]]=1
for s,sg in [('L',1),('R',-1)]:
 ids=np.where((pv==1)&(co[:,0]*sg>0))[0]
 sh,cl=J(f'B_{s}_UpperArm'),J(f'B_{s}_Clavicle');d=(sh-cl)/np.linalg.norm(sh-cl)
 for i in ids:
  inward=(co[i]-sh)@d
  keep=np.clip(1+inward/.07,0,1)
  for n in [f'B_{s}_UpperArm',f'B_{s}_UpperArmTwist']:
   dw=W[i,gi[n]]*(1-keep);W[i,gi[n]]-=dw;W[i,gi[f'B_{s}_Clavicle']]+=dw
# No shoulder or arm pull on the chin, moustache, eyes and hair.
head_ids=np.where((pv==1)&(co[:,2]>1.46)&(abs(co[:,0])<.11))[0]
headshare=np.clip((co[head_ids,2]-1.46)/.07,0,1)
for i,a in zip(head_ids,headshare):
 W[i]*=1-a;W[i,gi['B_Head']]+=a
hair={3,12,15,16,17,22,23,24,25,26,27,116}
for part in np.unique(pv):
 ids=np.where(pv==part)[0]
 if part in (1,2):continue
 if part in hair:bone='B_Head'
 elif part==4:bone='B_R_Hand'
 elif part==5:bone='B_L_Hand'
 elif part==6:bone='B_R_Calf'
 elif part==7:bone='B_L_Calf'
 elif part==13:bone='B_R_ForearmTwist'
 elif part==14:bone='B_L_ForearmTwist'
 elif part in (8,9,10,11,18,29,30,110):bone='B_Pelvis'
 else:bone='B_Spine2'
 rigid(ids,bone)
 print('RULE',int(part),'vertices',len(ids),bone)
# Diffuse the abrupt Meshy armpit transition over the sleeve surface.
adj=[[] for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==1 and pv[b]==1:adj[a].append(b);adj[b].append(a)
for _ in range(8):
 U=W.copy()
 for i in np.where((pv==1)&(abs(co[:,0])>.12)&(co[:,2]<1.43))[0]:
  if adj[i]:U[i]=.5*W[i]+.5*W[adj[i]].mean(0)
 W=U
# Dense gloves remain entirely on their hand until connectivity-based finger weights are applied.
assert np.isfinite(W).all() and np.max(abs(W.sum(1)-1))<1e-5
body.vertex_groups.clear()
for n in names:body.vertex_groups.new(name=n)
for i,row in enumerate(W):
 for j in np.flatnonzero(row>1e-5):body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
