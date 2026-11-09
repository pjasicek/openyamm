import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
s=json.loads((P/'work/round8/running_world.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round8_before/export/mm6_dwa1.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={}
correction={n:Matrix(s['rest'][n]).inverted()@rig.matrix_world@rig.data.bones[n].matrix_local for n in s['rest']}
for i,pose in enumerate(s['poses']):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 for pb in rig.pose.bones:
  if pb.name in pose:pb.matrix=rig.matrix_world.inverted()@Matrix(pose[pb.name])@correction[pb.name];bpy.context.view_layer.update()
 rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 for pb in rig.pose.bones:
  q=pb.rotation_quaternion.copy()
  if pb.name in prev and q.dot(prev[pb.name])<0:q=-q
  prev[pb.name]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=s['times'][i]*scene.render.fps);pb.keyframe_insert('location',frame=s['times'][i]*scene.render.fps)
a.use_frame_range=True;a.frame_start=0;a.frame_end=.8*scene.render.fps
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_dwa1.blend'))
print('EDITABLE Running replaced; geometry/materials/other actions retained')
