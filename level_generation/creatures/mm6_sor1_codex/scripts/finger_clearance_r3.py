"""Fit the off-hand skin through its full closing path, keeping its fixed palm frame."""
import bpy,numpy as np,json
from mathutils import Vector

def fit(rig,body,grip):
 scene=bpy.context.scene;me=body.data;ids=[v.index for v in me.vertices if me.attributes['piece'].data[v.index].value==4];groups=[g.name for g in body.vertex_groups];weights={i:[(groups[g.group],g.weight) for g in me.vertices[i].groups] for i in ids};inv={n:b.matrix_local.inverted() for n,b in rig.data.bones.items()};original=np.array([v.co[:] for v in me.vertices]);act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
 for iteration in range(4):
  updates={};worst=0
  for frame in [*range(66,116),*range(185,225)]:
   scene.frame_set(frame);H=rig.pose.bones['B_R_Hand'].matrix;C=H@Vector(grip['handle_centre_hand_local']);A=(H.to_3x3()@Vector(grip['handle_axis_hand_local'])).normalized();C+=A*.5;ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([em.vertices[i].co[:] for i in ids]);ev.to_mesh_clear();ds=co-np.array(C);along=ds@np.array(A);radial=ds-along[:,None]*np.array(A);radius=np.linalg.norm(radial,axis=1);transforms={}
   for j in np.where((abs(along)<.09)&(radius<.013))[0]:
    i=ids[int(j)];delta=radial[j]/max(radius[j],1e-8)*(.013-radius[j]);worst=max(worst,float(np.linalg.norm(delta)))
    for name,w in weights[i]:
     if name not in transforms:transforms[name]=np.array((rig.pose.bones[name].matrix@inv[name]).to_3x3())
    D=sum(w*transforms[name] for name,w in weights[i]);d=np.linalg.solve(D,delta)
    if np.linalg.norm(d)>np.linalg.norm(updates.get(i,np.zeros(3))):updates[i]=d
  rows.append({'iteration':iteration,'vertices':len(updates),'max_clearance_correction_mm':worst*1000})
  for i,d in updates.items():me.vertices[i].co+=Vector(d)
  me.update()
  if worst<.00005:break
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();dist=np.linalg.norm(np.array([v.co[:] for v in me.vertices])-original,axis=1);report={'iterations':rows,'changed_vertices':int((dist>1e-7).sum()),'max_rest_change_mm':float(dist.max()*1000),'palm_frame_and_rig_unchanged':True,'clearance_radius_mm':13};print('FINGER_FIT',report,flush=True);assert dist.max()<.012,report
 return report
