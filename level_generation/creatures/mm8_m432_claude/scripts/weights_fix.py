"""Gloves, fitted segmented clothing, rigid pauldrons, hair and small fasteners."""
import bpy,json,sys
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=o.data
c=np.array([v.co[:] for v in me.vertices]);pv=np.array([p.value for p in me.attributes['piece'].data])
names=[g.name for g in o.vertex_groups];gi={n:i for i,n in enumerate(names)};w=np.zeros((len(c),len(names)))
for v in me.vertices:
    for e in v.groups:w[v.index,e.group]=e.weight
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
for side in 'LR':
    sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local)
    keep=np.clip((np.abs(c[:,0])-abs(sh[0])+.07)/.07,0,1)
    for name in (f'B_{side}_UpperArm',f'B_{side}_UpperArmTwist'):
        idx=gi[name];removed=w[:,idx]*(1-keep);w[:,idx]*=keep;w[:,gi[f'B_{side}_Clavicle']]+=removed
# Face and hair have no arm influence; the visible neck blends smoothly to its base.
for i in np.where(np.isin(pv,[1,2,9,10,11]))[0]:
    t=float(np.clip((c[i,2]-1.62)/.06,0,1)) if pv[i]==1 else 1.
    w[i]=0;w[i,gi['B_Head']]=t;w[i,gi['B_Neck']]=1-t
for side,part in [('R',5),('L',6)]:
    ids=np.where(pv==part)[0];w[ids]=0;w[ids,gi[f'B_{side}_Hand']]=1
for side,part in [('L',3),('R',4)]:
    ids=np.where(pv==part)[0];allowed=[gi[n] for n in (f'B_{side}_Calf',f'B_{side}_Foot')]
    q=w[ids][:,allowed];q[:,1]+=w[ids,gi[f'B_{side}_Toe0']];q/=np.maximum(q.sum(1,keepdims=True),1e-9);w[ids]=0
    w[np.ix_(ids,allowed)]=q
skin=np.where(pv==0)[0];kd=KDTree(len(skin))
for i in skin:kd.insert(c[i],int(i))
kd.balance()
for part in sorted(set(pv)):
    if part<7 or part in (9,10,11):continue
    ids=np.where(pv==part)[0]
    refs=[kd.find(c[i])[1] for i in ids];avg=w[refs].mean(0)
    w[ids]=0
    if part in (7,8):
        side='R' if part==7 else 'L'
        allowed=[gi[f'B_{side}_Clavicle'],gi[f'B_{side}_UpperArm']]
        weights=avg[allowed];weights/=max(weights.sum(),1e-9)
        w[np.ix_(ids,allowed)]=weights
    else:w[ids,int(np.argmax(avg))]=1
assert np.isfinite(w).all() and np.allclose(w.sum(1),1,atol=.001), [(int(p),float(w[pv==p].sum(1).min()),float(w[pv==p].sum(1).max())) for p in sorted(set(pv)) if not np.allclose(w[pv==p].sum(1),1,atol=.001)]
for g in list(o.vertex_groups):o.vertex_groups.remove(g)
for n in names:o.vertex_groups.new(name=n)
for i in range(len(c)):
    for j in np.where(w[i]>1e-5)[0]:o.vertex_groups[int(j)].add([i],float(w[i,j]),'REPLACE')
garment=np.zeros(len(c),np.int32)
garment[np.isin(pv,[1,9,10])]=1;garment[np.isin(pv,[2,11])]=2;garment[np.isin(pv,[3,4])]=3
garment[np.isin(pv,[5,6])]=4;garment[np.isin(pv,[7,8])]=5;garment[pv>=12]=6
attr=me.attributes.get('garment') or me.attributes.new('garment','INT','POINT');attr.data.foreach_set('value',garment)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('WEIGHTS rules applied',dict(zip(*np.unique(garment,return_counts=True))))
