"""Troll skin ownership, rigid cranial details and pelvis-owned cloth before helper fitting."""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig=bpy.data.objects['Rig']; body=bpy.data.objects['Body']; me=body.data
co=np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv=len(co)
pv=np.zeros(nv,np.int32); me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups]; gi={n:i for i,n in enumerate(names)}
Wt=np.zeros((nv,len(names)))
for v in me.vertices:
    for e in v.groups: Wt[v.index,e.group]=e.weight
Wt/=np.maximum(Wt.sum(1,keepdims=True),1e-9)
J=lambda n: np.array(rig.data.bones[n].head_local)
skinids=np.where(pv==0)[0]
kd=KDTree(len(skinids))
for i in skinids: kd.insert(co[i],int(i))
kd.balance()
for piece in np.unique(pv):
    if piece==0: continue
    ids=np.where(pv==piece)[0]
    name='B_Pelvis' if piece in (1,2,16,17,65) else 'B_Head'
    if name=='B_Head' and co[ids,2].min()<1.32:
        for i in ids:
            hits=kd.find_n(co[i],4); weight=np.array([1/max(h[2],1e-4) for h in hits])
            Wt[i]=(Wt[[h[1] for h in hits]]*weight[:,None]).sum(0)/weight.sum()
    else:
        Wt[ids]=0; Wt[ids,gi[name]]=1
# 4. shoulder fade on the skin
moved = 0
skin = np.where(pv == 0)[0]
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)                       # clavicle direction, pointing out to the shoulder
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    for i in skin:
        m = (co[i] - sh) @ d                                        # > 0 outside the joint, < 0 toward the midline
        if m < 0 and Wt[i, ua] > 0:
            keep = max(0.0, 1.0 + m / 0.07)
            dw = Wt[i, ua] * (1 - keep)
            Wt[i, ua] -= dw; Wt[i, cv] += dw; moved += dw > 1e-3
print('RULE shoulder fade: skin vertices changed', moved)
# 5. jaw free of the shoulders (gob2 review 2): Meshy weighted even the jaw underside 21-37 % to the clavicles/upper
#    arms, so a shrug dragged the jaw down onto the shoulder. Skin above the jaw line (B_Head joint - 2 cm, ramp over
#    3 cm below it) inside the neck's width loses that weight to the neck/head; the side of the neck below keeps it and
#    still lifts with a shrug (a first version cleaned the whole neck above the clavicles: the jaw then stayed put and
#    the shoulder met it 5 cm deep instead of 2 cm).
jz = J('B_Head')[2] - 0.02; nz = J('B_Neck')[2]; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm', 'UpperArmTwist'))]
neck_moved = 0
for i in skin:
    fz = float(np.clip((co[i, 2] - (jz - 0.03)) / 0.03, 0, 1))
    if fz <= 0:
        continue
    keep_lat = float(np.clip((abs(co[i, 0] - ax_x) - 0.07) / 0.07, 0, 1))
    r = fz * (1 - keep_lat)
    dw = Wt[i, SH].sum() * r
    if dw > 1e-4:
        Wt[i, SH] *= (1 - r)
        Wt[i, gi['B_Head'] if co[i, 2] > jz else gi['B_Neck']] += dw; neck_moved += 1
print('RULE jaw free of the shoulders: skin vertices changed', neck_moved)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
