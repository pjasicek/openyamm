"""Fit the deformed hand surface to the generated handle, including triangle interiors."""
import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fingers.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];g=json.loads((p/'work/grip_pose.json').read_text())
rig.animation_data.action=bpy.data.actions['GripRef'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(8)
snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
for n,q in g['finger_local'].items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q
bpy.context.view_layer.update();H=(rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix).inverted()
c=np.array(g['handle_centre_hand_local']);R=Vector((0,0,1)).rotation_difference(Vector(g['handle_axis_hand_local'])).to_matrix();inv=np.array(R.inverted())
with bpy.data.libraries.load(str(p/'work/club_clean.blend'),link=False) as (src,dst):dst.objects=['ClubMesh']
club=dst.objects[0];tree=BVHTree.FromPolygons([tuple(v.co) for v in club.data.vertices],[tuple(f.vertices) for f in club.data.polygons],all_triangles=True)
me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data]);lab=np.array([a.value for a in me.attributes['finger'].data])
me.calc_loop_triangles()
tri=np.array([f.vertices[:] for f in me.loop_triangles if all(pv[i]==2 for i in f.vertices)],dtype=int)
assert len(tri)>100
labels=np.array([np.bincount(lab[t],minlength=6).argmax() for t in tri])
bary=np.array([[1/3]*3,[.5,.5,0],[0,.5,.5],[.5,0,.5],[1,0,0],[0,1,0],[0,0,1]])
groups=[]
names=[v.name for v in body.vertex_groups]
for tag in ['B_R_Hand']+[f'B_R_Finger{i}' for i in range(5)]:
 w=np.array([sum(e.weight for e in v.groups if names[e.group]==tag or (tag!='B_R_Hand' and names[e.group].startswith(tag))) for v in me.vertices])
 groups.append(np.einsum('sk,tk->ts',bary,w[tri]).ravel()>.3)
def distances():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
 co=np.empty(len(em.vertices)*3);em.vertices.foreach_get('co',co);ev.to_mesh_clear();co=co.reshape(-1,3)
 world=np.einsum('sk,tkj->tsj',bary,co[tri]).reshape(-1,3)
 local=(np.c_[world,np.ones(len(world))]@np.array(H).T)[:,:3];local=(local-c)@inv.T
 sel=(abs(local[:,2])<.17)&(np.linalg.norm(local[:,:2],axis=1)<.12)
 ds=np.full(len(local),1.0)
 for i in np.flatnonzero(sel):
  q,n,face,d=tree.find_nearest(Vector(local[i]));sign=-1 if (Vector(local[i])-q).dot(n)<0 else 1;ds[i]=d*sign
 return ds
def cost():
 ds=distances();value=0;rows=[]
 for i in range(6):
  d=ds[groups[i]];pen=max(0.,-float(d.min()));gap=float(np.abs(d).min());rows.append((pen,gap))
  value+=40*pen*pen+20*max(gap-.0015,0)**2+5*float(np.minimum(d,0)@np.minimum(d,0))/len(d)
 return value,rows
print('ACTUAL_GRIP before',cost(),flush=True)
for step in (12,6,3,1.5):
 for name in g['finger_local']:
  pb=rig.pose.bones[name]
  for axis in ((1,0,0),(0,1,0),(0,0,1)):
   original=pb.rotation_quaternion.copy();best=original;score=cost()[0]
   for sign in (-1,1):
    pb.rotation_quaternion=original@Quaternion(Vector(axis),math.radians(step*sign));s=cost()[0]
    if s<score:score=s;best=pb.rotation_quaternion.copy()
   pb.rotation_quaternion=best
 # Move the shaft within the palm only after every digit can contribute.
 for axis in range(3):
  original=c.copy();best=c.copy();score=cost()[0]
  for sign in (-1,1):
   c=original.copy();c[axis]+=sign*step*.0002;s=cost()[0]
   if s<score:score=s;best=c.copy()
  c=best
 print('ACTUAL_GRIP step',step,cost(),flush=True)
g['finger_local']={n:list(rig.pose.bones[n].rotation_quaternion) for n in g['finger_local']};g['handle_centre_hand_local']=c.tolist();g['actual_surface_fit']=cost()[1]
(p/'work/grip_pose.json').write_text(json.dumps(g,indent=2))
assert all(np.isfinite(q).all() for q in g['finger_local'].values())
