"""Component ownership for the dark-elf tunic, loose sleeves, hands, boots and hair."""
import bpy, sys, numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body']; me=body.data
co=np.array([tuple(v.co) for v in me.vertices]); nv=len(co)
pv=np.zeros(nv,np.int32); me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups]; gi={n:i for i,n in enumerate(names)}
W=np.zeros((nv,len(names)))
for v in me.vertices:
    for e in v.groups: W[v.index,e.group]=e.weight

def keep(ids, allowed, fallback):
    cols=[gi[n] for n in allowed]
    row=W[ids].copy(); row[:,[j for j in range(len(names)) if j not in cols]]=0
    bad=row.sum(1)<1e-6; row[bad,gi[fallback]]=1
    W[ids]=row/row.sum(1,keepdims=True)

def rigid(piece, bone):
    ids=np.flatnonzero(np.isin(pv,piece)); W[ids]=0; W[ids,gi[bone]]=1

rigid([1,9,10,15,16],'B_Head')
for side,hand,sleeve,boot,tabs in [('L',3,7,6,[12,13]),('R',4,8,5,[11,14])]:
    rigid([hand],f'B_{side}_Hand')
    arm=[f'B_{side}_{x}' for x in ('Clavicle','UpperArm','Forearm','Hand')]
    ids=np.flatnonzero(pv==sleeve)
    keep(ids,arm,'B_'+side+'_UpperArm')
    keep(np.flatnonzero(pv==boot),[f'B_{side}_{x}' for x in ('Calf','Foot','Toe0')],f'B_{side}_Calf')
    for tab in tabs:
        ti=np.flatnonzero(pv==tab)
        centre=co[ti].mean(0)
        nearest=ids[np.argsort(np.linalg.norm(co[ids]-centre,axis=1))[:12]]
        W[ti]=W[nearest].mean(0)
# The torso includes the short tunic; upper-arm weights must not pull its neck or chest.
keep(np.flatnonzero(pv==0),['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head',
    'B_L_Clavicle','B_R_Clavicle','B_L_Thigh','B_R_Thigh'],'B_Spine2')
keep(np.flatnonzero(pv==2),['B_Pelvis','B_L_Thigh','B_R_Thigh','B_L_Calf','B_R_Calf'],'B_Pelvis')
# Blend the tunic hem into the corresponding thigh without stretching across the crotch.
ids=np.flatnonzero((pv==0)&(co[:,2]<1.02))
a=np.clip((1.02-co[ids,2])/.17,0,1)*.60
left=np.clip(.5+co[ids,0]/.16,0,1)
W[ids]=0; W[ids,gi['B_Pelvis']]=1-a
W[ids,gi['B_L_Thigh']]=a*left; W[ids,gi['B_R_Thigh']]=a*(1-left)
assert np.allclose(W.sum(1),1) and np.isfinite(W).all()
for g in list(body.vertex_groups): body.vertex_groups.remove(g)
for n in names: body.vertex_groups.new(name=n)
for i,row in enumerate(W):
    for j in np.flatnonzero(row>1e-5): body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_owned.blend'))
print('RULE component ownership checked', {int(p):int((pv==p).sum()) for p in np.unique(pv)})
