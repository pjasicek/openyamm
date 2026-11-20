"""Remove torso bleed from the upper arms and smooth short-edge cloth weight discontinuities."""
from pathlib import Path
import bpy,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_animated.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data;nv=len(me.vertices);co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);cr=np.array([x.value for x in me.attributes['cloth_region'].data]);W=np.zeros((nv,len(o.vertex_groups)));names=[g.name for g in o.vertex_groups]
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
for s,sign in [('L',1),('R',-1)]:
 sh=np.array(r.data.bones[f'B_{s}_UpperArm'].head_local);el=np.array(r.data.bones[f'B_{s}_Forearm'].head_local);d=el-sh;t=(co-sh)@d/(d@d)
 arm=[i for i,n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in ['UpperArm','Forearm'])];spine=[i for i,n in enumerate(names) if n in ['B_Spine','B_Spine1','B_Spine2']]
 mask=(pv==0)&(cr==0)&(co[:,0]*sign>.145)&(W[:,arm].sum(1)>.4)&(t>.25)
 dst=names.index(f'B_{s}_UpperArm');W[mask,dst]+=W[np.ix_(mask,spine)].sum(1);W[np.ix_(mask,spine)]=0
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]:
  w=1/max(.001,float(np.linalg.norm(co[a]-co[b])));adj[a].append((b,w));adj[b].append((a,w))
mask=((pv==0)&(abs(co[:,0])>.14)&(cr!=1))|(pv==1)
for _ in range(8):
 nxt=W.copy()
 for i in np.where(mask)[0]:
  if adj[i]:
   ids,weight=zip(*adj[i]);weight=np.array(weight);nxt[i]=.5*W[i]+.5*(W[list(ids)]*weight[:,None]).sum(0)/weight.sum()
 W=nxt
retained=[]
for i,w in enumerate(W):
 keep=np.argsort(-w)[:8];total=w[keep].sum();retained.append(float(total));new=np.zeros_like(w);new[keep]=w[keep]/total;W[i]=new
assert min(retained)>.94,min(retained)
for g in o.vertex_groups:g.remove(list(range(nv)))
for i,w in enumerate(W):
 assert abs(w.sum()-1)<1e-5
 for j in np.where(w>1e-6)[0]:o.vertex_groups[int(j)].add([i],float(w[j]),'REPLACE')
# The provisional v1 trouser waist was wider than the selected v2 robe; fit this concealed overlap locally.
for v in me.vertices:
 if pv[v.index]==12:
  t=float(np.clip((v.co.z-.90)/.14,0,1));centre=np.array(r.data.bones['B_Pelvis'].head_local)
  v.co.x=centre[0]+(v.co.x-centre[0])*(1-.22*t)
  v.co.y=centre[1]+(v.co.y-centre[1])*(1-.22*t)
print('WEIGHT_POLISH',int(mask.sum()),'minimum retained mass',min(retained))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_polished.blend'))
