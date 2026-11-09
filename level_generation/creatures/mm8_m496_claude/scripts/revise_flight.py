"""Replace only Walking/Running on the retained packed master; leave geometry, materials and other clips alone."""
import bpy,importlib.util,math
from pathlib import Path
p=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fire_model',p/'scripts/build_model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
bpy.ops.wm.open_mainfile(filepath=str(p/'archive/pre_native_flight/export/mm8_m496.blend'))
rig=bpy.data.objects['FireElemental_Rig'];scene=bpy.context.scene
for name,seconds in [('Walking',1.0),('Running',.8)]:
 old=bpy.data.actions.get(name)
 rig.animation_data_clear()
 if old:bpy.data.actions.remove(old)
 action=bpy.data.actions.new(name);action.use_fake_user=True;model.assign(rig,action)
 previous={};count=round(seconds*model.FPS)
 for frame in range(count+1):
  phase=2*math.pi*frame/count
  model.flight_pose(rig,phase)
  rig.pose.bones['AshRoot'].scale=(model.HIDDEN,)*3
  for side in ['Left','Right']:rig.pose.bones['Burst'+side].scale=(model.HIDDEN,)*3
  for bone in rig.pose.bones:
   q=bone.rotation_quaternion.copy()
   if bone.name in previous and q.dot(previous[bone.name])<0:q.negate()
   previous[bone.name]=q.copy();bone.rotation_quaternion=q
   for prop in ['location','rotation_quaternion','scale']:bone.keyframe_insert(prop,frame=frame+1)
 for curve in model.action_curves(action):
  for key in curve.keyframe_points:key.interpolation='LINEAR'
 print('FLIGHT',name,count+1)
model.assign(rig,bpy.data.actions['Standing']);scene.frame_set(1);bpy.context.view_layer.update()
objects=[obj for obj in bpy.data.objects if obj.type=='MESH']
model.save_export(rig,objects)
