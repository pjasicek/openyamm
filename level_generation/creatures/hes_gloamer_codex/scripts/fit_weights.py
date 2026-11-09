"""Correct the measured head/back ownership and shoulder leakage; teeth are rigid, pores follow nearby skin."""
import bpy,json,sys,os
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fingers.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;co=np.array([v.co[:] for v in me.vertices])
piece=np.array([v.value for v in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
original=W.copy();skin=np.where(piece==0)[0]
axial=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];axcols=[gi[n] for n in axial]+[gi['B_Neck'],gi['B_Head']]
heights=np.array([rig.data.bones[n].head_local.z for n in axial]);assert (np.diff(heights)>0).all()
def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
for i in skin:
    share=W[i,axcols].sum();W[i,axcols]=0
    core=float(smooth((.22-abs(co[i,0]))/.10)*smooth((co[i,2]-.85)/.08))
    for side in ['L','R']:
        for part in ['Clavicle','UpperArm']:
            j=gi['B_'+side+'_'+part];moved=W[i,j]*core;W[i,j]-=moved;share+=moved
    z=co[i,2];k=int(np.clip(np.searchsorted(heights,z)-1,0,len(heights)-2));t=float(np.clip((z-heights[k])/(heights[k+1]-heights[k]),0,1))
    W[i,gi[axial[k]]]=share*(1-t);W[i,gi[axial[k+1]]]=share*t
    for side in ['L','R']:
        sh=np.array(rig.data.bones['B_'+side+'_UpperArm'].head_local);cl=np.array(rig.data.bones['B_'+side+'_Clavicle'].head_local)
        direction=(sh-cl)/np.linalg.norm(sh-cl);ac=gi['B_'+side+'_UpperArm'];cc=gi['B_'+side+'_Clavicle']
        keep=float(smooth(((co[i]-sh)@direction+.08)/.08));moved=W[i,ac]*(1-keep);W[i,ac]-=moved;W[i,cc]+=moved
    # The projecting jaw and skull move as the head; the high posterior hump belongs to the trunk.
    head=float(smooth((-.015-co[i,1])/.095)*smooth((co[i,2]-1.16)/.055))
    if head>0:
        W[i]*=1-head;W[i,gi['B_Head']]+=head
kd=KDTree(len(skin))
for j,i in enumerate(skin):kd.insert(co[i],j)
kd.balance()
pores=set(json.loads((P/'review/geometry/cleanup.json').read_text())['pores_flattened'])
for pid in set(piece)-{0}:
    ids=np.where(piece==pid)[0]
    if pid not in pores:
        W[ids]=0;W[ids,gi['B_Head']]=1
    else:
        for i in ids:
            hits=kd.find_n(co[i],4);weights=np.array([1/max(h[2],.0001) for h in hits]);weights/=weights.sum()
            W[i]=sum(W[skin[h[1]]]*w for h,w in zip(hits,weights))
assert np.isfinite(W).all() and (W>=-1e-8).all()
W/=W.sum(1,keepdims=True)
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i in range(len(co)):
    for j in np.where(W[i]>.0001)[0]:body.vertex_groups[int(j)].add([i],float(W[i,j]),'REPLACE')
report={'changed_vertices':int((np.abs(W-original).max(1)>.001).sum()),'head_dominant':int((W[:,gi['B_Head']]>.5).sum()),'hump_head_weight_max':float(W[(co[:,1]>.08)&(co[:,2]>1.4)&(piece==0),gi['B_Head']].max())}
assert report['hump_head_weight_max']==0
(P/'review/geometry/weight_corrections.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
print('WEIGHT FIT',report,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
