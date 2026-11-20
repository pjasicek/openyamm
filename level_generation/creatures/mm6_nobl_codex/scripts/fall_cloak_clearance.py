"""Give the falling cloak a smooth clearance arch over the boots; keep the final corpse unchanged."""
import bpy,numpy as np,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v11.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv);co=np.array([v.co[:] for v in me.vertices])
clothfaces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==0 for i in f.vertices) and np.mean(co[list(f.vertices),2])<1.2]
bootids=np.flatnonzero((pv==2)&(co[:,2]<.14))
names=[b.name for b in r.data.bones if b.name.startswith('Cloak_')]
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
original=[];basis=[]
for f in range(56):
 sc.frame_set(f);original.append({n:r.pose.bones[n].matrix.copy() for n in names})
 basis.append({n:r.pose.bones[n].matrix_basis.copy() for n in names})
def posed():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();X=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();return X
def penetration():
 X=posed();tree=BVHTree.FromPolygons(X,clothfaces);maximum=0
 for i in bootids:
  v=X[int(i)];hit,normal,k,d=tree.ray_cast(v+Vector((0,0,.7)),Vector((0,0,-1)),1.4)
  if hit is not None:maximum=max(maximum,v.z+.008-hit.z)
 return maximum
before=[];after=[]
# A broad, differentiable lift follows the cloth's fall and settles before Dead.
for f in range(56):
 sc.frame_set(f);before.append(penetration())
 t=(f-11)/31
 bump=math.sin(math.pi*t)**2 if 0<t<1 else 0
 desired={}
 for n in names:
  k=int(n.rsplit('_',1)[1]);M=original[f][n].copy()
  M.translation.z+=bump*[.035,.12,.20,.175][k];desired[n]=M
 for n in names:
  b=r.pose.bones[n];parent=desired.get(b.parent.name,r.pose.bones[b.parent.name].matrix)
  local=(parent@rest[b.parent.name].inverted()@rest[n]).inverted()@desired[n]
  b.location=local.translation;b.rotation_mode='QUATERNION';b.rotation_quaternion=local.to_quaternion()
  b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f)
 bpy.context.view_layer.update();after.append(penetration())
print('CLOAK_BOOT_CLEARANCE',json.dumps({'before_mm':np.round(np.array(before)*1000,2).tolist(),'after_mm':np.round(np.array(after)*1000,2).tolist()}))
(p/'review/feet_cloak_20261011/fall_cloak_clearance.json').write_text(json.dumps({'before_mm':(np.array(before)*1000).tolist(),'after_mm':(np.array(after)*1000).tolist()},indent=1))
assert max(after)<.001, max(after)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v12.blend'))
