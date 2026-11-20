"""Correct diagnosed torso/opposite-limb ownership and keep stone feet rigid."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];co=np.array([v.co[:] for v in body.data.vertices]);names=[g.name for g in body.vertex_groups];ix={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
for v in body.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
clamp=lambda x:np.clip(x,0,1)
def smooth(x):
 x=clamp(x);return x*x*(3-2*x)
# Restore service weights for the shoulder vertices inadvertently covered by the first skull-height rule.
# Their nearest service vertices are unchanged, so this is an exact transfer.
from mathutils.kdtree import KDTree
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/rig_v1/result_rigged_character_glb_url.glb'))
new=set(bpy.data.objects)-before;mesh=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices))
mc=np.array([tuple(mesh.matrix_world@v.co) for v in mesh.data.vertices]);scale=np.ptp(co[:,2])/np.ptp(mc[:,2]);centre=lambda a:np.array([(a[:,0].min()+a[:,0].max())/2,(a[:,1].min()+a[:,1].max())/2,a[:,2].min()])
mc=mc*scale+centre(co)-centre(mc)*scale;kd=KDTree(len(mc))
for i,c in enumerate(mc):kd.insert(c,i)
kd.balance()
mapping={'Hips':'B_Pelvis','Spine02':'B_Spine','Spine01':'B_Spine1','Spine':'B_Spine2','neck':'B_Neck','Head':'B_Head','head_end':'B_Head','headfront':'B_Head'}
for sd,long in [('L','Left'),('R','Right')]:
 for dst,src in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:mapping[long+src]=f'B_{sd}_{dst}'
for vi,c in enumerate(co):
 if c[2]>2.01 and (abs(c[0]+.036)>.24 or c[1]>.12) and c[2]<2.14:
  _,j,dist=kd.find(c);assert dist<.003;W[vi]=0
  for g in mesh.data.vertices[j].groups:W[vi,ix[mapping[mesh.vertex_groups[g.group].name]]]+=g.weight
for o in new:bpy.data.objects.remove(o,do_unlink=True)
# Midline back/chest mistakenly followed arms and thighs; blend it onto its actual axial joints.
chain=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'];zs=np.array([rig.data.bones[n].head_local.z for n in chain])
originalW=W.copy()
fist_mask=np.zeros(len(co),bool)
for sd,sg in [('L',1),('R',-1)]:
 wr=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local)
 ownership=W[:,ix[f'B_{sd}_Hand']]+W[:,ix[f'B_{sd}_Forearm']]
 fist_mask|=(co[:,0]*sg>.23)&(co[:,1]<-.12)&(np.linalg.norm(co-wr,axis=1)<.42)&(ownership>.5)
for vi,(x,y,z) in enumerate(co):
 if 1.08<z<1.99 and not fist_mask[vi]:
  width=float(np.interp(z,[1.08,1.25,1.55,1.80,1.99],[.19,.27,.39,.35,.15]))
  amount=smooth((width-abs(x))/.14)*smooth((z-1.08)/.20)*smooth((1.99-z)/.10)*smooth((y+.34)/.10)
  if amount>0:
   zc=max(zs[0],min(zs[-1],z));j=int(np.clip(np.searchsorted(zs,zc)-1,0,len(zs)-2));t=(zc-zs[j])/(zs[j+1]-zs[j]);T=np.zeros(len(names));T[ix[chain[j]]]=1-t;T[ix[chain[j+1]]]=t
   W[vi]=W[vi]*(1-amount)+T*amount
 # Shoulder slabs are separated from the skull by their position, not height alone.
 h=smooth((z-1.94)/.17)*smooth((.30-abs(x+.036))/.07)*smooth((.18-y)/.08)
 if z>2.14:h=1
 if h>0:W[vi]*=1-h;W[vi,ix['B_Head']]+=h
 if z<1.15:
  sd,other=('L','R') if x>0 else ('R','L')
  for part in ['Thigh','Calf','Foot','Toe0']:
   a,b=ix[f'B_{other}_{part}'],ix[f'B_{sd}_{part}'];amount=float(smooth((abs(x)-.02)/.07+(1.0-z)/.10));moved=W[vi,a]*amount;W[vi,b]+=moved;W[vi,a]-=moved
for sd in ['L','R']:
 a,b=ix[f'B_{sd}_Toe0'],ix[f'B_{sd}_Foot'];W[:,b]+=W[:,a];W[:,a]=0
# Smooth repaired transitions on connected surfaces, preserving rigid fist cores.
adj=[[] for _ in co]
for e in body.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
mask=(co[:,2]>1.12)&(co[:,2]<2.15)&(co[:,1]>-.16)
for _ in range(5):
 nextW=W.copy()
 for i in np.where(mask)[0]:
  if adj[i]:nextW[i]=W[i]*.55+W[adj[i]].mean(0)*.45
 W=nextW
# Smooth continuous pelvis-to-thigh weights on the groin; avoid a seam at the midline.
for i,(x,y,z) in enumerate(co):
 if z<1.42 and z>.76 and abs(x)<.28 and y>-.20 and not fist_mask[i]:
  l,r,pel=[ix[n] for n in ['B_L_Thigh','B_R_Thigh','B_Pelvis']]
  amount=float(smooth((z-.76)/.18)*smooth((.28-abs(x))/.10))
  if amount:
   left=float(smooth((x+.15)/.30));hip=float(smooth((z-1.04)/.29))
   target=np.zeros(len(names));target[pel]=hip;target[l]=(1-hip)*left;target[r]=(1-hip)*(1-left)
   W[i]=W[i]*(1-amount)+target*amount
W[fist_mask]=originalW[fist_mask]
for i,w in enumerate(W):
 w[w<.001]=0
 if np.count_nonzero(w)>8:w[np.argsort(w)[:-8]]=0
 assert w.sum()>.1;W[i]=w/w.sum()
body.vertex_groups.clear();groups=[body.vertex_groups.new(name=n) for n in names]
for i,w in enumerate(W):
 for j in np.where(w>0)[0]:groups[j].add([i],float(w[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v6.blend'))
print('WEIGHTS repaired',int(mask.sum()),'torso/shoulder vertices; rigid stone feet')
