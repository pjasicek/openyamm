"""Keep skin deformation continuous and each piece of the ogre's armor on its anatomical owner."""
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
# End the exposed arm skin beneath the bands/bracers; its generated open ends show during the raise.
bm=bmesh.new();bm.from_mesh(me);part=bm.verts.layers.int['piece']
edges={e for e in bm.edges if e.is_boundary and all(v[part]==0 for v in e.verts)};pending=set(edges);caps=[]
while pending:
 todo=[pending.pop()];component=set()
 while todo:
  e=todo.pop();component.add(e)
  for v in e.verts:
   for other in v.link_edges:
    if other in pending:pending.remove(other);todo.append(other)
 verts=set(v for e in component for v in e.verts);center=sum((v.co for v in verts),start=__import__('mathutils').Vector())/len(verts)
 if abs(center.x)>.2 and .85<center.z<1.22:
  result=bmesh.ops.holes_fill(bm,edges=list(component));caps.extend(result['faces'])
if caps:
 bmesh.ops.triangulate(bm,faces=caps)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(me);bm.free();print('ARM_SKIN closed covered arm ends',len(caps))
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
def rigid(parts,bone):
 ids=np.flatnonzero(np.isin(pv,parts));W[ids]=0;W[ids,gi[bone]]=1
for side,hand in [('L',3),('R',2)]:rigid([hand],f'B_{side}_Hand')
# The heavy jaw must stay on the skull while the neck blends into the broad trapezius.
ids=np.flatnonzero((pv==0)&(np.abs(co[:,0])<.15)&(co[:,2]>.1))
a=np.clip((co[ids,2]-.4*co[ids,1]-1.425)/.045,0,1)
W[ids]*=1-a[:,None];W[ids,gi['B_Head']]+=a
for side in ('L','R'):
 sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local);cl=np.array(rig.data.bones[f'B_{side}_Clavicle'].head_local)
 d=(sh-cl)/np.linalg.norm(sh-cl);ids=np.flatnonzero(pv==0)
 fade=np.clip(-((co[ids]-sh)@d)/.07,0,1);amount=W[ids,gi[f'B_{side}_UpperArm']]*fade
 W[ids,gi[f'B_{side}_UpperArm']]-=amount;W[ids,gi[f'B_{side}_Clavicle']]+=amount
skin=np.flatnonzero(np.isin(pv,[0,1,2,3,4,5]));kd=KDTree(len(skin))
for i,j in enumerate(skin):kd.insert(co[j],i)
kd.balance()
def underlying(point):
 hits=kd.find_n(point,4);weight=np.array([1/max(h[2],1e-4) for h in hits]);weight/=weight.sum()
 return (W[[skin[h[1]] for h in hits]]*weight[:,None]).sum(0)
for part in np.unique(pv):
 if part<6:continue
 ids=np.flatnonzero(pv==part)
 if part>=100:rigid([part],'B_Head')
 elif part in (7,9):W[ids]=np.array([underlying(co[i]) for i in ids])
 elif part in (28,31):
  a=np.clip((.86-co[ids,2])/.28,0,1)*.65;left=np.clip(.5+co[ids,0]/.16,0,1)
  W[ids]=0;W[ids,gi['B_Pelvis']]=1-a;W[ids,gi['B_L_Thigh']]=a*left;W[ids,gi['B_R_Thigh']]=a*(1-left)
 else:
  row=underlying(co[ids].mean(0));bone=names[int(np.argmax(row))];rigid([part],bone)
for side,parts in [('L',[6,16,60]),('R',[8,17,61])]:rigid(parts,f'B_{side}_Calf')
for side,parts in [('L',[19,24]),('R',[18,23])]:rigid(parts,f'B_{side}_Forearm')
rigid([21],'B_L_UpperArm');rigid([22],'B_R_UpperArm')
rigid([12,32,50,65,66],'B_L_Clavicle');rigid([13,27],'B_Pelvis')
assert np.isfinite(W).all() and np.allclose(W.sum(1),1,atol=1e-5)
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i,row in enumerate(W):
 for j in np.flatnonzero(row>1e-5):body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_owned.blend'))
print('OWNERSHIP normalized skin, armor, cloth and head',len(co))
