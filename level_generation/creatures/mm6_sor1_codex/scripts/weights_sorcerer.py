import bpy,sys,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);nv=len(co)
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
w=np.zeros((nv,len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight

def assign(ids,weights):
 w[ids]=0
 for n,a in weights.items():w[ids,gi[n]]=a
for piece,sd in [(3,'R'),(4,'L')]:assign(pv==piece,{f'B_{sd}_Hand':1})
for piece in [5,7,8,13,14,15]:assign(pv==piece,{'B_Head':1})
ids=np.where(pv==2)[0]
h=np.clip((co[ids,2]-1.41)/.06,0,1)
assign(ids,{'B_Head':h,'B_Neck':1-h})
assign(np.isin(pv,[6,12,*range(16,33)]),{'B_Pelvis':.7,'B_Spine':.3})
assign(pv==11,{'B_Spine2':1})
# Small shoulder ornaments follow each clavicle instead of stretching over the arm bend.
for piece in [9,10]:
 ids=np.where(pv==piece)[0];sd='L' if co[ids,0].mean()>0 else 'R';assign(ids,{f'B_{sd}_Clavicle':1})
# Tall collar belongs to the upper robe, independently of the head.
ids=np.where((pv==1)&(co[:,2]>1.41))[0];assign(ids,{'B_Spine2':1})
# The sleeve owns only its arm channels; hip weights are invalid across the open air gap.
for sd,sign in [('R',-1),('L',1)]:
 ids=np.where((pv==1)&(sign*co[:,0]>.22))[0]
 keep=[gi[n] for n in names if n.startswith('B_'+sd+'_') and any(x in n for x in ['Clavicle','UpperArm','Forearm','Hand'])]
 mask=np.zeros(len(names));mask[keep]=1;w[ids]*=mask
 w[ids]/=np.maximum(w[ids].sum(1,keepdims=True),1e-9)
# Lower robe is a separate cloth surface. Exposed shoes below the hem follow their own foot.
assign(pv==100,{'B_Pelvis':1})
for sd,piece in [('R',101),('L',102)]:assign(pv==piece,{f'B_{sd}_Foot':1})
# Diffuse the sleeve/torso junction using its topology; do not cross unrelated shells.
adj=[[] for _ in range(nv)]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==1:adj[a].append(b);adj[b].append(a)
ids=np.where((pv==1)&(abs(co[:,0])>.10)&(abs(co[:,0])<.26)&(co[:,2]>1.14)&(co[:,2]<1.41))[0]
for _ in range(12):
 nw=w.copy()
 for i in ids:
  if adj[i]:nw[i]=.5*w[i]+.5*w[adj[i]].mean(0)
 w=nw
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
assert np.allclose(w.sum(1),1,atol=.001)
body.vertex_groups.clear()
for name in names:body.vertex_groups.new(name=name)
for i,row in enumerate(w):
 for j in np.where(row>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
me.attributes['piece'].data.foreach_set('value',pv.tolist())
# Generated hidden bridges joined the shoes to the skirt; open these seams under the hem.
import bmesh
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
bad=[f for f in bm.faces if len({int(pv[v.index]) for v in f.verts})>1 and any(pv[v.index]>=100 for v in f.verts)]
print('REMOVE shoe/robe bridges',len(bad));bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY');bm.to_mesh(me);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_weights.blend'))
