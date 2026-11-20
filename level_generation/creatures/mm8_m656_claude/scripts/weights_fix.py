"""Mercenary armour weights: rigid shells, cuff ownership, and articulated tassets."""
import bpy, sys
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(src))
body=bpy.data.objects['Body']; rig=bpy.data.objects['Rig']; me=body.data
co=np.array([tuple(v.co) for v in me.vertices]); pv=np.array([v.value for v in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups]; gi={n:i for i,n in enumerate(names)}
w=np.zeros((len(co),len(names)))
for v in me.vertices:
    for e in v.groups: w[v.index,e.group]=e.weight
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
def rigid(piece,bone):
    ids=np.where(pv==piece)[0]; w[ids]=0;w[ids,gi[bone]]=1
    print('RULE',piece,'rigid',bone,len(ids))
for piece in (5,8,17,18,19,21,22,27,84,85): rigid(piece,'B_Head')
for piece,bone in {2:'B_R_Hand',3:'B_L_Hand',9:'B_L_Clavicle',10:'B_R_Clavicle',11:'B_L_ForearmTwist',13:'B_R_ForearmTwist',14:'B_L_UpperArm',15:'B_R_UpperArm',20:'B_L_Forearm',23:'B_R_Forearm',25:'B_R_Calf',26:'B_L_Calf',28:'B_R_Forearm',29:'B_L_Forearm',30:'B_L_Forearm',31:'B_R_Forearm',12:'B_Pelvis',24:'B_Pelvis',83:'B_Pelvis'}.items(): rigid(piece,bone)
# Glove cuffs meet a moving hand; the bracers finish before this wrist hinge.
for side in ('R','L'):
    sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local)
    cl=np.array(rig.data.bones[f'B_{side}_Clavicle'].head_local)
    direction=(sh-cl)/np.linalg.norm(sh-cl)
    arm=gi[f'B_{side}_UpperArm']; cv=gi[f'B_{side}_Clavicle']
    ids=np.where(pv==0)[0]; medial=(co[ids]-sh)@direction
    remove=w[ids,arm]*(1-np.clip(1+medial/0.07,0,1))
    w[ids,arm]-=remove; w[ids,cv]+=remove
for piece in range(32,43):
    ids=np.where(pv==piece)[0]; cen=co[ids].mean(0)
    bone='B_Pelvis' if cen[2]>.7 else f'B_{"L" if cen[0]>0 else "R"}_Calf'
    rigid(piece,bone)
# Each tasset keeps one shared pelvis/thigh blend, so its plate remains flat.
for piece in list(range(43,83))+[16]:
    ids=np.where(pv==piece)[0]; w[ids]=0
    for i in ids:
        c=co[i] if piece==16 else co[ids].mean(0)
        thigh=np.clip((.97-c[2])/.26,0,1)*.65
        left=np.clip((c[0]+.04)/.08,0,1)
        w[i,gi['B_Pelvis']]=1-thigh
        w[i,gi['B_L_Thigh']]=thigh*left
        w[i,gi['B_R_Thigh']]=thigh*(1-left)
# Spread the sleeve/torso junction over adjacent rows rather than one stretched edge.
neighbours=[[] for _ in co]
for edge in me.edges:
    a,b=edge.vertices
    if pv[a]==0 and pv[b]==0:neighbours[a].append(b);neighbours[b].append(a)
for _ in range(3):
    new=w.copy()
    for i in np.where(pv==0)[0]:
        if neighbours[i]:new[i]=.5*w[i]+.5*w[neighbours[i]].mean(0)
    w=new
# Cap influences for the renderer, preserving the strongest four.
for i in range(len(w)):
    keep=np.argsort(w[i])[-4:]; row=np.zeros(len(names));row[keep]=w[i,keep];w[i]=row/max(row.sum(),1e-9)
assert np.allclose(w.sum(1),1,atol=1e-5), 'Unweighted vertices'
body.vertex_groups.clear()
for n in names:body.vertex_groups.new(name=n)
for i in range(len(w)):
    for j in np.where(w[i]>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(w[i,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(out))
