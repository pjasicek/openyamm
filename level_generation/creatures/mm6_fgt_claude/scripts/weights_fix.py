"""Thug-specific shell weights: rigid fittings, articulated tassets, clean shoulder/head influences."""
import bpy,sys,os,json
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);nv=len(co)
pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
w=np.zeros((nv,len(names)))
for v in me.vertices:
 for e in v.groups:w[v.index,e.group]=e.weight
assert np.all(w.sum(1)>0), 'Unweighted geometry'
w/=w.sum(1,keepdims=True)
J=lambda n:np.array(rig.data.bones[n].head_local)
# Torso and arms share a shell; remove shoulder influence toward the chest midline before copying fittings.
for side in ('R','L'):
 sh,cl=J(f'B_{side}_UpperArm'),J(f'B_{side}_Clavicle');d=(sh-cl)/np.linalg.norm(sh-cl)
 m=(co-sh)@d;fade=np.clip(1+m/.07,0,1)
 ids=np.where((pv==0)&(m<0))[0]
 for name in ('UpperArm','UpperArmTwist'):
  col=gi[f'B_{side}_{name}'];moved=w[ids,col]*(1-fade[ids]);w[ids,col]-=moved
  w[ids,gi['B_Spine2']]+=moved
# Head, hair and sideburns have no shoulder or arm deformation; a short neck band blends into Neck.
for part in (1,3,26,27):
 ids=np.where(pv==part)[0];a=np.clip((co[ids,2]-1.38)/.07,0,1)
 w[ids]=0;w[ids,gi['B_Neck']]=1-a;w[ids,gi['B_Head']]=a
surface=np.where(np.isin(pv,(0,1,2,4,5)))[0]
kd=KDTree(len(surface))
for k,i in enumerate(surface):kd.insert(co[i],k)
kd.balance()
strips={16,17,18,19,20,21,22,23,24,25,28,30,31,33,34,36,38}
rigid_pelvis={6,8,10,14,15,39,40,45,47}
for part in sorted(set(pv.tolist())-set((0,1,2,3,4,5,26,27))):
 ids=np.where(pv==part)[0];c=co[ids].mean(0)
 if part in rigid_pelvis:
  w[ids]=0;w[ids,gi['B_Pelvis']]=1;rule='pelvis fitting'
 elif part in strips:
  # Match the trouser surface's pelvis/thigh share, keeping one left/right mixture across the strip.
  near=[]
  for i in ids:
   hits=kd.find_n(co[i],4);ww=np.array([1/max(h[2],1e-4) for h in hits])
   near.append((ww[:,None]*w[[surface[h[1]] for h in hits]]).sum(0)/ww.sum())
  near=np.array(near);left=near[:,gi['B_L_Thigh']];right=near[:,gi['B_R_Thigh']]
  a=np.clip(left+right,0,1);wl=float(left.sum()/max((left+right).sum(),1e-9))
  w[ids]=0;w[ids,gi['B_Pelvis']]=1-a;w[ids,gi['B_L_Thigh']]=a*wl;w[ids,gi['B_R_Thigh']]=a*(1-wl);rule=f'tasset surface share L={wl:.2f}'
 elif part in (11,12):
  side='R' if c[0]<0 else 'L';w[ids]=0;w[ids,gi[f'B_{side}_UpperArmTwist']]=1;rule='rigid shoulder cap'
 elif part in (7,13):
  side='R' if part==7 else 'L';w[ids]=0
  # P07 contains the right pauldron and the scarf tail as a single connected mesh. The scarf follows the back.
  scarf=(co[ids,1]>.11)&(co[ids,2]<1.34) if part==7 else np.zeros(len(ids),bool)
  clav=np.clip((np.abs(co[ids[~scarf],0])-.06)/.18,0,.6)
  w[ids[~scarf],gi[f'B_{side}_Clavicle']]=clav;w[ids[~scarf],gi['B_Spine2']]=1-clav
  w[ids[scarf],gi['B_Spine2']]=1;rule='pauldron with back scarf'
 else:
  nw=[]
  for i in ids:
   hits=kd.find_n(co[i],4);a=np.array([1/max(h[2],1e-4) for h in hits])
   nw.append((a[:,None]*w[[surface[h[1]] for h in hits]]).sum(0)/a.sum())
  w[ids]=nw;rule='surface copy'
  if part in (9,41,42,43,44,46):
   arm=[gi[n] for n in names if any(x in n for x in ('Arm','Hand','Finger'))]
   w[np.ix_(ids,arm)]=0
 print('RULE',part,len(ids),rule)
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
assert np.allclose(w.sum(1),1), 'Weight normalization'
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i in range(nv):
 for j in np.where(w[i]>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(w[i,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
