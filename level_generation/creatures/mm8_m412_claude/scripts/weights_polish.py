"""Remove distant-bone contamination and smooth the shirt's shoulder transition."""
import bpy,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src);o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in o.vertex_groups];gi={n:i for i,n in enumerate(names)}
w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
# Torso weights follow the actual axial joint heights, without thigh/arm influences across the chest opening.
ax=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck'];zz=[rig.data.bones[n].head_local.z for n in ax]
A=np.zeros_like(w)
for i,c in enumerate(co):
 z=min(c[2],zz[-2]+(zz[-1]-zz[-2])*.3);k=max(0,min(len(ax)-2,int(np.searchsorted(zz,z))-1));t=np.clip((z-zz[k])/(zz[k+1]-zz[k]),0,1)
 A[i,gi[ax[k]]]=1-t;A[i,gi[ax[k+1]]]=t
arms=[j for j,n in enumerate(names) if any(s in n for s in ['Clavicle','UpperArm','Forearm','Hand'])]
shirt=np.where(pv==0)[0];arm=w[:,arms].copy()
for k,j in enumerate(arms):
 sg=1 if '_L_' in names[j] else -1
 arm[:,k]*=np.clip((co[:,0]*sg-.075)/.15,0,1)
# Spatially weighted neighbour averaging preserves short-edge continuity at folds and seam vertices.
nb=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==0:
  d=np.linalg.norm(co[a]-co[b]);nb[a].append((b,1/max(d,.002)));nb[b].append((a,1/max(d,.002)))
for _ in range(20):
 nw=arm.copy()
 for i in shirt:
  if nb[i]:
   ix,weights=zip(*nb[i]);weights=np.array(weights);nw[i]=.5*arm[i]+.5*np.average(arm[list(ix)],axis=0,weights=weights)
 arm=nw
w[shirt]=A[shirt]*(1-arm[shirt].sum(1,keepdims=True));w[np.ix_(shirt,arms)]+=arm[shirt]
# Exposed neck/chest use a smooth axial transition; the facial region is rigid on Head.
for i in np.where(pv==1)[0]:
 z=co[i,2];w[i]=0
 if z<1.36:w[i,gi['B_Spine2']]=1
 elif z<1.43:
  t=(z-1.36)/.07;w[i,gi['B_Spine2']]=1-t;w[i,gi['B_Neck']]=t
 else:
  t=np.clip((z-1.43)/.04,0,1);w[i,gi['B_Neck']]=1-t;w[i,gi['B_Head']]=t
allowed=[j for j,n in enumerate(names) if n=='B_Pelvis' or any(x in n for x in ['Thigh','Calf'])]
for j in range(len(names)):
 if j not in allowed:w[pv==2,j]=0
mask=(pv==2)&(co[:,2]>1.0);w[mask]=0;w[mask,gi['B_Pelvis']]=1
assert np.all(w.sum(1)>1e-5);w/=w.sum(1,keepdims=True)
for g in list(o.vertex_groups):o.vertex_groups.remove(g)
for n in names:o.vertex_groups.new(name=n)
for i,row in enumerate(w):
 for j in np.where(row>1e-5)[0]:o.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
print('POLISH',len(shirt),'shirt vertices')
bpy.ops.wm.save_as_mainfile(filepath=out)
