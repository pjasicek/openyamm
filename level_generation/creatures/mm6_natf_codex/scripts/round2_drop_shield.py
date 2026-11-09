"""Release the shield during the fall; it settles independently beside the corpse."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_cloth.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;b=rig.pose.bones['LeafShield'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];release=.12;land=.45
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];sc.frame_set(0);hold_q=b.rotation_quaternion.copy();hold_l=b.location.copy();rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in list(range(math.ceil(release*60)))+[release*60]:
 sc.frame_set(int(f),subframe=f%1);b.rotation_quaternion=hold_q;b.location=hold_l;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
sc.frame_set(int(release*60),subframe=release*60%1);start=b.matrix.copy();q0=start.to_quaternion();q1=Matrix.Rotation(math.pi/2,4,'X').to_quaternion();ob=bpy.data.objects['LeafShield'];iv=rig.data.bones['LeafShield'].matrix_local.inverted();co=np.array([tuple(iv@v.co)for v in ob.data.vertices]);target=Vector((.78,.85,0));target.z=.009-float((co@np.array(q1.to_matrix()).T)[:,2].min());prev=None
for f in range(math.ceil(release*60),int(a.frame_range[1])+1):
 t=f/60;u=max(0,min(1,(t-release)/(land-release)));ease=u*u*(3-2*u);q=q0.slerp(q1,ease);pos=start.translation.lerp(target,ease);pos.z+=.05*math.sin(math.pi*u);pos.z=max(pos.z,.009-float((co@np.array(q.to_matrix()).T)[:,2].min()));M=q.to_matrix().to_4x4();M.translation=pos;sc.frame_set(f);b.matrix=M;bpy.context.view_layer.update()
 if prev is not None and b.rotation_quaternion.dot(prev)<0:b.rotation_quaternion=-b.rotation_quaternion
 prev=b.rotation_quaternion.copy();b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
sc.frame_set(int(a.frame_range[1]));end=b.matrix.copy();dead=bpy.data.actions['Dead'];rig.animation_data.action=dead;rig.animation_data.action_slot=dead.slots[0]
for f in range(int(dead.frame_range[1])+1):
 sc.frame_set(f);b.matrix=end;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for act in [a,dead]:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'LeafShield' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_cloth.blend'));(P/'review/round2/shield_release.json').write_text(json.dumps({'release_s':release,'land_s':land,'final_origin':list(target),'reason':'Avoid lifting the corpse to clear a still-gripped shield corner; released prop settles beside the body.'},indent=2))
