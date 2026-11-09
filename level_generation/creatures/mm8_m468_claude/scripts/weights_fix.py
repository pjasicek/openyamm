"""Vampire garment ownership, independent jaw and longer upper fangs."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data])
# The selected references show long outer upper canines, distinct from the incisors.
for part in (8,11):
 ids=np.flatnonzero(pv==part);top=co[ids,2].max()
 for i in ids:me.vertices[int(i)].co.z=top+(co[i,2]-top)*1.65
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones.new('B_Jaw');eb.head=(-.005,-.105,1.491);eb.tail=(-.005,-.205,1.449);eb.parent=rig.data.edit_bones['B_Head']
bpy.ops.object.mode_set(mode='OBJECT');body.vertex_groups.new(name='B_Jaw')
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
def rigid(ids,bone):W[ids]=0;W[ids,gi[bone]]=1
# Prevent the skin under the jaw and the pointed ears inheriting shoulder/clavicle motion.
ids=np.flatnonzero(pv==0)
neck=np.clip((co[ids,2]-1.37)/.10,0,1)*np.clip((.19-np.abs(co[ids,0]))/.10,0,1)
W[ids]*=1-neck[:,None];W[ids,gi['B_Neck']]+=neck
a=np.clip((co[ids,2]-.6*co[ids,1]-1.48)/.055,0,1)*np.clip((.20-np.abs(co[ids,0]))/.08,0,1)
W[ids,gi['B_Neck']]+=W[ids,gi['B_Head']];W[ids,gi['B_Head']]=0
W[ids]*=1-a[:,None];W[ids,gi['B_Head']]+=a
rigid(np.flatnonzero(pv>=5),'B_Head')
# Mouth halves: upper gums and fangs stay on the skull; only the chin, lower lip/teeth and tongue hinge.
ids=np.flatnonzero((pv==0)&(co[:,2]<1.493)&(co[:,2]>1.410)&(co[:,1]<-.105))
a=np.clip((1.493-co[ids,2])/.025,0,1)*np.clip((-.105-co[ids,1])/.025,0,1)
W[ids]*=1-a[:,None];W[ids,gi['B_Jaw']]+=a
rigid(np.flatnonzero(np.isin(pv,[7,12,13,14])),'B_Jaw')
# Soft garments follow their nearby skin; the belt and buckle remain on the pelvis.
skin=np.flatnonzero(pv==0);kd=KDTree(len(skin))
for j,i in enumerate(skin):kd.insert(co[i],j)
kd.balance()
for i in np.flatnonzero(np.isin(pv,[1,2])):
 hits=kd.find_n(co[i],3);weights=np.array([1/max(h[2],.003)**2 for h in hits]);weights/=weights.sum()
 W[i]=(W[[skin[h[1]] for h in hits]]*weights[:,None]).sum(0)
rigid(np.flatnonzero(np.isin(pv,[3,4])),'B_Pelvis')
for sd in 'LR':
 wrist=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local);elbow=np.array(rig.data.bones[f'B_{sd}_Forearm'].head_local);d=wrist-elbow;d/=np.linalg.norm(d)
 ids=np.flatnonzero((pv==0)&(np.sign(co[:,0])==np.sign(wrist[0]))&(np.linalg.norm(co-wrist,axis=1)<.34)&((co-wrist)@d>.012));rigid(ids,f'B_{sd}_Hand')
assert np.isfinite(W).all() and np.allclose(W.sum(1),1,atol=1e-5)
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i,row in enumerate(W):
 for j in np.flatnonzero(row>1e-5):body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_owned.blend'))
print('OWNERSHIP',len(co),'vertices; jaw, skull, skin, soft garments, belt')
