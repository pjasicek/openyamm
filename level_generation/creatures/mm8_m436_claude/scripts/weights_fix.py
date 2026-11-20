"""Continuous skin, torso-owned vest, rigid leather pack and fitted finger bases."""
from pathlib import Path
import bpy,numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
def rigid(ids,bone):W[ids]=0;W[ids,gi[bone]]=1
ids=np.flatnonzero((pv==0)&(np.abs(co[:,0]+.03)<.25)&(co[:,2]>1.30));a=np.clip((co[ids,2]-.5*co[ids,1]-1.50)/.055,0,1);W[ids]*=1-a[:,None];W[ids,gi['B_Head']]+=a
for side in 'LR':
 sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{side}_Clavicle'].head_local);d=(sh-cl)/np.linalg.norm(sh-cl);ids=np.flatnonzero(pv==0);fade=np.clip(-((co[ids]-sh)@d)/.08,0,1)*np.clip((co[ids,2]-1.20)/.10,0,1);amount=W[ids,gi[f'B_{side}_UpperArm']]*fade;W[ids,gi[f'B_{side}_UpperArm']]-=amount;W[ids,gi[f'B_{side}_Clavicle']]+=amount
 el=np.array(rig.data.bones[f'B_{side}_Forearm'].head_local);wr=np.array(rig.data.bones[f'B_{side}_Hand'].head_local);d=(wr-el)/np.linalg.norm(wr-el);ids=np.flatnonzero((pv==0)&(co[:,0]*(1 if side=='L' else -1)>.35)&(co[:,2]>.55));a=np.clip(((co[ids]-wr)@d+.012)/.025,0,1);W[ids]*=1-a[:,None];W[ids,gi[f'B_{side}_Hand']]+=a
# Meshy leaked hip/torso influence into the thick inner elbows; use the measured arm cross-sections.
for side,sign in [('L',1),('R',-1)]:
 sh,el,wr=[np.array(rig.data.bones[f'B_{side}_{n}'].head_local) for n in ('UpperArm','Forearm','Hand')];u=el-sh;v=wr-el;du=u/np.linalg.norm(u);dv=v/np.linalg.norm(v);tu=(co-sh)@u/(u@u);tf=(co-el)@v/(v@v);radU=np.linalg.norm(co-sh-np.outer(np.clip(tu,0,1),u),axis=1);radF=np.linalg.norm(co-el-np.outer(np.clip(tf,0,1),v),axis=1);ids=np.flatnonzero((pv==0)&(co[:,0]*sign>.26)&(co[:,2]>.65)&(np.minimum(radU,radF)<.14)&(tu>.02));axis=(du+dv)/np.linalg.norm(du+dv);a=np.clip(((co[ids]-el)@axis+.055)/.11,0,1);a=a*a*(3-2*a);h=np.clip(((co[ids]-wr)@dv+.025)/.055,0,1);h=h*h*(3-2*h);blend=np.clip((tu[ids]-.02)/.25,0,1);new=np.zeros_like(W[ids]);new[:,gi[f'B_{side}_UpperArm']]=(1-a)*(1-h);new[:,gi[f'B_{side}_Forearm']]=a*(1-h);new[:,gi[f'B_{side}_Hand']]=h;W[ids]=W[ids]*(1-blend[:,None])+new*blend[:,None]
# Blend across the anatomical ownership boundary, keeping the palm and digits untouched.
nb=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;nb[a].append(b);nb[b].append(a)
ids=np.flatnonzero((pv==0)&(np.abs(co[:,0])>.22)&(co[:,2]>.87)&(co[:,2]<1.43))
for _ in range(10):
 V=W.copy()
 for i in ids:
  ns=[j for j in nb[i] if pv[j]==0]
  if ns:V[i]=.5*W[i]+.5*W[ns].mean(0)
 W=V
skin=np.flatnonzero(pv==0);kd=KDTree(len(skin))
for i,j in enumerate(skin):kd.insert(co[j],i)
kd.balance()
def underlying(point):
 hits=kd.find_n(point,4);w=np.array([1/max(h[2],1e-4) for h in hits]);w/=w.sum();return (W[[skin[h[1]] for h in hits]]*w[:,None]).sum(0)
for part in np.unique(pv):
 if part==0:continue
 ids=np.flatnonzero(pv==part)
 if part==105:
  rigid(ids,'B_Head')
  for i in ids:
   if co[i,2]<1.60:
    a=float(np.clip((co[i,2]-1.44)/.16,0,1));row=underlying(co[i]);W[i]*=a;W[i]+=row*(1-a)
 elif part>=100:rigid(ids,'B_Head')
 elif part in (3,4,5,8,9):rigid(ids,'B_Spine2')
 elif part in (6,7):rigid(ids,'B_Pelvis')
 elif part==1:
  W[ids]=0
  for i in ids:
   x,y,z=co[i];cl=float(np.clip((abs(x+.03)-.13)/.16,0,1))*float(np.clip((z-1.10)/.16,0,1));t=float(np.clip((z-1.0)/.30,0,1));W[i,gi['B_Spine1']]=(1-cl)*(1-t);W[i,gi['B_Spine2']]=(1-cl)*t;W[i,gi['B_L_Clavicle' if x>-.03 else 'B_R_Clavicle']]=cl
   neck=float(np.clip((z-1.36)/.09,0,1))*float(np.clip((.23-abs(x+.03))/.08,0,1));W[i]=W[i]*(1-neck)+underlying(co[i])*neck
 else:W[ids]=np.array([underlying(co[i]) for i in ids])
assert np.isfinite(W).all() and np.allclose(W.sum(1),1,atol=1e-5)
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i,row in enumerate(W):
 for j in np.flatnonzero(row>1e-5):body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_owned.blend'))
print('OWNERSHIP',len(co),'vertices')
