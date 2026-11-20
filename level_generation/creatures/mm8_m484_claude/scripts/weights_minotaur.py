"""Assign MM8 skin, harness, mane, kilt and rigid cloven hooves to their anatomical owners."""
import bpy,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2t.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);ng=[g.name for g in b.vertex_groups];ix={n:i for i,n in enumerate(ng)};W=np.zeros((len(co),len(ng)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
# The skull, horns, ears and muzzle are rigid; a narrow neck transition remains below the jaw.
head=((pv==0)&(co[:,2]>1.52))|np.isin(pv,[5,6,8]);W[head]=0;W[head,ix['B_Head']]=1
for sd,sgn in [('L',1),('R',-1)]:
 foot=(pv==1)&(co[:,0]*sgn>0)&(co[:,2]<.20);W[foot]=0;W[foot,ix[f'B_{sd}_Foot']]=1
 # Small wrist cuff follows distal forearm roll; soft wrist skin blends into the hand.
 el=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);wr=np.array(r.data.bones[f'B_{sd}_Hand'].head_local);d=wr-el;t=(co-el)@d/(d@d)
 band=(pv==0)&(co[:,0]*sgn>.4)&(t>.55)&(t<1.05)
 for i in np.where(band)[0]:
  a=np.clip((t[i]-.55)/.15,0,1);hand=np.clip((t[i]-.96)/.09,0,1);old=W[i].copy();want=np.zeros(len(ng));want[ix[f'B_{sd}_ForearmTwist']]=1-hand;want[ix[f'B_{sd}_Hand']]=hand;W[i]=(1-a)*old+a*want
# A fingertip never keeps an auto-rig forearm fraction; it creates a rigid bridge through the fist.
for sd,sgn in [('L',1),('R',-1)]:
 el=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);wr=np.array(r.data.bones[f'B_{sd}_Hand'].head_local);d=wr-el;d/=np.linalg.norm(d);beyond=(co-wr)@d
 mask=(pv==0)&(co[:,0]*sgn>.45)&(beyond>-.01)
 share=np.clip((beyond+.01)/.06,0,1)
 W[mask]*=(1-share[mask,None]);W[mask,ix[f'B_{sd}_Hand']]+=share[mask]
 # Remove distant pelvis/thigh ownership from the arm and arm ownership from the medial ribs.
 arm=[i for i,n in enumerate(ng) if n.startswith(f'B_{sd}_') and any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]
 fade=np.clip((co[:,0]*sgn-(.205+.3*np.clip(co[:,2]-1.10,0,.30)))/.06,0,1);removed=W[:,arm].sum(1)*(1-fade);W[:,arm]*=fade[:,None];upper=np.clip((co[:,2]-1.30)/.12,0,1);W[:,ix[f'B_{sd}_Clavicle']]+=removed*upper;W[:,ix['B_Spine1']]+=removed*(1-upper)
 own=np.clip((co[:,0]*sgn-(.215+.3*np.clip(co[:,2]-1.10,0,.30)))/.045,0,1)*np.clip((1.40-co[:,2])/.10,0,1)*(pv==0)
 trunk=[ix[n] for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2',f'B_{sd}_Clavicle',f'B_{sd}_Thigh']]
 moved=W[:,trunk].sum(1)*own;W[:,trunk]*=1-own[:,None];mix=np.clip((co[:,2]-el[2]+.04)/.1,0,1);W[:,ix[f'B_{sd}_UpperArm']]+=moved*mix;W[:,ix[f'B_{sd}_Forearm']]+=moved*(1-mix)
# Hip, head and opposite-limb weights are invalid on upper-arm skin; consolidate its torso contribution.
for sd,sgn in [('L',1),('R',-1)]:
 mask=(pv==0)&(co[:,0]*sgn>.17)&(co[:,2]>1.10)&(co[:,2]<1.48)
 trunk=[i for i,n in enumerate(ng) if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'] or ('Thigh' in n)]
 amount=W[:,trunk].sum(1);W[np.ix_(np.where(mask)[0],trunk)]=0;W[mask,ix['B_Spine2']]+=amount[mask]
# Diffuse weight jumps along connected shoulder skin, without touching the fitted digits.
nb=[[] for _ in co]
for e in me.edges:
 v1,v2=e.vertices;nb[v1].append(v2);nb[v2].append(v1)
mask=(pv==0)&(abs(co[:,0])>.17)&(abs(co[:,0])<.49)&(co[:,2]>1.02)&(co[:,2]<1.45)
for _ in range(150):
 out=W.copy()
 for i in np.where(mask)[0]:
  if nb[i]:out[i]=.7*W[i]+.3*W[nb[i]].mean(0)
 W=out
# Consolidate the diffused shoulder channels before the four-influence export limit; dropping a different
# small torso bone on neighbouring vertices creates a discontinuity at the armpit.
for sd,sgn in [('L',1),('R',-1)]:
 mask=(pv==0)&(co[:,0]*sgn>.17)&(co[:,2]>1.05)&(co[:,2]<1.48)
 trunk=[i for i,n in enumerate(ng) if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'] or 'Thigh' in n]
 amount=W[:,trunk].sum(1);W[np.ix_(np.where(mask)[0],trunk)]=0;W[mask,ix['B_Spine2']]+=amount[mask]
 sh=np.array(r.data.bones[f'B_{sd}_UpperArm'].head_local);el=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);d=el-sh;t=(co-sh)@d/(d@d);fade=np.clip((.85-t)/.30,0,1)*mask
 cols=[ix[f'B_{sd}_Forearm'],ix[f'B_{sd}_ForearmTwist']];amount=W[:,cols].sum(1)*fade;W[:,cols]*=1-fade[:,None];W[:,ix[f'B_{sd}_UpperArm']]+=amount
skin=np.where(np.isin(pv,[0,1]))[0];kd=KDTree(len(skin))
for k,i in enumerate(skin):kd.insert(co[i],k)
kd.balance()
# Strap/stud fragments and mane cards inherit adjacent skin, never a passing arm.
access=(pv>=2)&(pv!=5)&(pv!=6)&(pv!=8)&(pv!=100)
for i in np.where(access)[0]:
 hits=kd.find_n(co[i],3);ww=np.array([1/max(h[2],.001) for h in hits]);W[i]=(W[[skin[h[1]] for h in hits]]*ww[:,None]).sum(0)/ww.sum()
# Short mail hangs from the belt. Thigh carry on the hem gives the first pose probe clearance.
for i in np.where(pv==100)[0]:
 W[i]=0;a=np.clip((.905-co[i,2])/.22,0,.65);sd='L' if co[i,0]>0 else 'R';W[i,ix['B_Pelvis']]=1-a;W[i,ix[f'B_{sd}_Thigh']]=a
# The runtime uses four skin influences; every subsequent probe uses the same limit.
keep=np.argsort(W,axis=1)[:,-4:];limited=np.zeros_like(W);rows=np.arange(len(W))[:,None];limited[rows,keep]=W[rows,keep];W=limited
assert np.isfinite(W).all() and (W.sum(1)>0).all();W/=W.sum(1)[:,None]
for g in b.vertex_groups:g.remove(list(range(len(co))))
for i,w in enumerate(W):
 for k in np.where(w>1e-5)[0]:b.vertex_groups[k].add([i],float(w[k]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'))
