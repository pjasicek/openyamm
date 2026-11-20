"""Triton rigid armour ownership and nearest-skin harness weights."""
import bpy,sys
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
body=bpy.data.objects['Body']; me=body.data
for side in 'LR':
    name=f'Pauldron_{side}'
    if name not in body.vertex_groups:body.vertex_groups.new(name=name)
co=np.array([tuple(v.co) for v in me.vertices]); piece=np.array([v.value for v in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups]; gi={n:i for i,n in enumerate(names)}
w=np.zeros((len(co),len(names)))
for v in me.vertices:
    for e in v.groups:w[v.index,e.group]=e.weight
for part,bone in {1:'B_Head',2:'B_Spine2',3:'Pauldron_L',4:'Pauldron_R',5:'B_L_UpperArm',6:'B_R_UpperArm',7:'B_Head',8:'B_Head',9:'B_Spine2'}.items():
    if bone.startswith('Pauldron') and bone not in bpy.data.objects['Rig'].data.bones:bone=f'B_{bone[-1]}_Clavicle'
    ids=np.where(piece==part)[0];w[ids]=0;w[ids,gi[bone]]=1
kd=KDTree(int((piece==0).sum()))
for i in np.where(piece==0)[0]:kd.insert(co[i],int(i))
kd.balance()
trunk=[gi[n] for n in ('B_Spine','B_Spine1','B_Spine2')]
for i in np.where(np.isin(piece,(10,11)))[0]:
    _,j,_=kd.find(co[i]);w[i]=0;w[i,trunk]=w[j,trunk]
    if w[i].sum()<.01:w[i,gi['B_Spine2']]=1
if 'finger' in me.attributes:
    digit=np.array([v.value for v in me.attributes['finger'].data])>0
    nonhand=[i for i,n in enumerate(names) if 'Hand' not in n and 'Finger' not in n]
    w[np.ix_(digit,nonhand)]=0
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
assert np.allclose(w.sum(1),1,atol=1e-5)
body.vertex_groups.clear()
for n in names:body.vertex_groups.new(name=n)
for i in range(len(w)):
    for j in np.where(w[i]>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(w[i,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
