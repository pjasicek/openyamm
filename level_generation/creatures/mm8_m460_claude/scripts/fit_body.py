"""Fit clothing ownership and preserve the independently measured hand skin weights."""
from pathlib import Path
import bpy,json,sys,runpy,os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
p=Path(__file__).resolve().parents[1]
s=p/'scripts/twist_bones.py';sys.argv=[str(s),'--',str(p/'work/motion_sources.blend'),str(p/'work/motion_twist.blend')]
os.environ['FA_RAMP']='0.15,0.85';os.environ['FA']='0.6';runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
for v in me.vertices:
    for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-10)
spines=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];zs=np.array([rig.data.bones[n].head_local.z for n in spines])
def trunk(z):
    j=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[j])/(zs[j+1]-zs[j]),0,1));r=np.zeros(len(names));r[gi[spines[j]]]=1-t;r[gi[spines[j+1]]]=t;return r
for sd in 'LR':
    sh=np.array(rig.data.bones[f'B_{sd}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{sd}_Clavicle'].head_local);ax=sh-cl;ax/=np.linalg.norm(ax)
    keep=np.clip(1+(co-sh)@ax/.065,0,1)
    for n in [f'B_{sd}_UpperArm',f'B_{sd}_UpperArmTwist']:
        moved=W[:,gi[n]]*(1-keep)*(pv==0);W[:,gi[n]]-=moved;W[:,gi[f'B_{sd}_Clavicle']]+=moved
    foot=(pv==0)&(co[:,0]*(1 if sd=='L' else -1)>0)&(co[:,2]<.18)
    for i in np.where(foot)[0]:
        amount=float(np.clip((.18-co[i,2])/.06,0,1));W[i]*=1-amount;W[i,gi[f'B_{sd}_Foot']]+=amount
for i in np.where((pv==0)&(co[:,2]>1.05)&(co[:,2]<1.43)&(abs(co[:,0])<.14))[0]:
    amount=float(np.clip((.14-abs(co[i,0]))/.06,0,1));W[i]=W[i]*(1-amount)+trunk(co[i,2])*amount
for i in np.where((pv==0)&(co[:,2]>1.40)&(abs(co[:,0])<.11))[0]:
    z=co[i,2];t=float(np.clip((z-1.42)/.06,0,1));W[i]=0;W[i,gi['B_Neck']]=1-t;W[i,gi['B_Head']]=t
me.calc_loop_triangles();tris=[t for t in me.loop_triangles if all(pv[i]==0 for i in t.vertices)]
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in tris],all_triangles=True)
for i in np.where(pv==1)[0]:
    x,y,z=co[i];W[i]=trunk(z)
    # Raised collar follows the shoulders; hair near the scalp follows the head.
    hair=abs(x)<.115 and z>1.35
    if hair:
        t=float(np.clip((z-1.39)/.17,0,1));W[i]*=1-t;W[i,gi['B_Head']]+=t
    if z<1.43:
        loc,normal,ti,distance=tree.find_nearest(Vector(co[i]),.04)
        if loc is not None:
            tri=tris[ti];bc=barycentric_transform(loc,*[me.vertices[j].co for j in tri.vertices],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
            weights=np.maximum(np.array(bc),0);weights/=weights.sum();W[i]=sum((W[j]*w for j,w in zip(tri.vertices,weights)),np.zeros(len(names)))
for part,bone in [(6,'B_Pelvis'),(17,'B_Pelvis'),(7,'B_Head'),(8,'B_Head'),(11,'B_Head'),(9,'B_R_ForearmTwist'),(10,'B_L_ForearmTwist')]:
    ids=np.where(pv==part)[0];W[ids]=0;W[ids,gi[bone]]=1
assert np.isfinite(W).all() and np.min(W.sum(1))>.99
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i in range(len(co)):
    for j in np.where(W[i]>.0001)[0]:body.vertex_groups[j].add([i],float(W[i,j]/W[i].sum()),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_skin.blend'))
print('Fitted skin, high collar, hair, cuffs, belt and boots.')
