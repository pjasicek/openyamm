"""Broaden the reduced mesh's knuckle weight blend (the male's separate sleeve-root rule does not apply: the sleeves
are part of piece 0, weighted by weights_fix.py) and keep 25 % of the source curl on the open left hand."""
import bpy, numpy as np
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'))
body=bpy.data.objects['Body']; rig=bpy.data.objects['Rig']; me=body.data
co=np.array([tuple(v.co) for v in me.vertices]); nv=len(co)
pv=np.zeros(nv,np.int32); me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups]; gi={n:i for i,n in enumerate(names)}
W=np.zeros((nv,len(names)))
for v in me.vertices:
    for e in v.groups: W[v.index,e.group]=e.weight
for sd,part in [('L',3),('R',4)]:
    cols=[gi[f'B_{sd}_Hand']]+[gi[f'B_{sd}_Finger{f}'] for f in range(5)]
    chans=W[:,cols].copy(); total=chans.sum(1)
    near=(pv==part)&(total>.01)
    edges=np.array([tuple(e.vertices) for e in me.edges]); edges=edges[(pv[edges[:,0]]==part)&(pv[edges[:,1]]==part)]
    for _ in range(6):
        acc=chans.copy(); degree=np.ones(nv)
        np.add.at(acc,edges[:,0],chans[edges[:,1]]); np.add.at(acc,edges[:,1],chans[edges[:,0]])
        np.add.at(degree,edges[:,0],1); np.add.at(degree,edges[:,1],1)
        avg=acc/degree[:,None]; sums=avg.sum(1)
        chans[near]=avg[near]/np.maximum(sums[near,None],1e-9)*total[near,None]
    W[:,cols]=chans
retained=[]
assert np.allclose(W.sum(1),1,atol=1e-4)
for v in me.vertices:
    row=W[v.index]; ix=np.argsort(row)[-4:]; total=row[ix].sum()
    retained.append(float(total))
    assert total>.80
    for e in list(v.groups): body.vertex_groups[e.group].remove([v.index])
    for j in ix:
        if row[j]>1e-5: body.vertex_groups[int(j)].add([v.index],float(row[j]/total),'REPLACE')
# The open left hand keeps a small natural source curl; it is not holding a weapon.
for act in bpy.data.actions:
    if not act.use_fake_user or act.name=='GripRef': continue
    rig.animation_data.action=act
    if len(act.slots): rig.animation_data.action_slot=act.slots[0]
    keys=[]
    for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        bpy.context.scene.frame_set(f)
        keys.append((f,{b.name:Quaternion().slerp(b.rotation_quaternion,.25) for b in rig.pose.bones if b.name.startswith('B_L_Finger')}))
    for f,pose in keys:
        for name,q in pose.items():
            pb=rig.pose.bones[name]; pb.rotation_quaternion=q; pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
print('RULE four-influence retained weight minimum',min(retained))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_refined.blend'))
print('RULE knuckle band smoothed; left source curl 25%')
