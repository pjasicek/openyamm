"""Preserve retained head deformation while keeping the new library death fit; audit original equipment winding."""
from pathlib import Path
import bpy,bmesh,sys,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10u.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rest=rig.data.bones['B_Head'].matrix_local.copy();deform=[]
for f in range(int(act.frame_range[1])+1):sc.frame_set(f);deform.append(rig.pose.bones['B_Head'].matrix@rest.inverted())
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones['B_Head'].translate(Vector((0,-.025,-.03)));bpy.ops.object.mode_set(mode='OBJECT')
# Rebind the fitted death to the original head joint. Other clips retain their original deformation transforms.
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rest=rig.data.bones['B_Head'].matrix_local
for f,d in enumerate(deform):
 sc.frame_set(f);pb=rig.pose.bones['B_Head'];pb.matrix=d@rest;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
sc.frame_set(int(act.frame_range[1]));held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones};bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in [0,30]:
 for n,(q,l) in held.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
for a in [a for a in bpy.data.actions if a.use_fake_user and a.name not in ['Death','Dead']]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in [a.frame_range[0],a.frame_range[1]]:
  pb=rig.pose.bones['B_Head'];pb.location=(0,0,0);pb.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
with bpy.data.libraries.load(str(p/'work/rig_v7.blend'),link=False) as (src,dst):dst.objects=['Body']
old=dst.objects[0];om=old.data;bm=bmesh.new();bm.from_mesh(body.data);pv=bm.verts.layers.int['piece'];flipped={}
for part in range(1,37):
 if part in [20,21]:continue
 faces=[f for f in om.polygons if all(om.attributes['piece'].data[i].value==part for i in f.vertices)]
 if not faces:continue
 tree=BVHTree.FromPolygons([v.co for v in om.vertices],[tuple(f.vertices) for f in faces])
 for f in bm.faces:
  if any(v[pv]!=part for v in f.verts):continue
  loc,n,fi,d=tree.find_nearest(f.calc_center_median());assert d<1e-4,(part,d)
  if f.normal.dot(n)<-.9:f.normal_flip();flipped[part]=flipped.get(part,0)+1
bm.to_mesh(body.data);bm.free();bpy.data.objects.remove(old,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v11.blend'));print('EQUIPMENT_WINDING_RESTORED',flipped)
