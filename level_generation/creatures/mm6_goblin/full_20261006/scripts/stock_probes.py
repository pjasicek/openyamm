"""Retarget included Meshy stock clips as deformation probes; never native replacements."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import author_pilots as P
import bpy
from mathutils import Quaternion,Matrix,Vector
P.sword.hide_render=True
report=[]
for kind in ['walk','run']:
 with bpy.data.libraries.load(str(P.OUT/f'work/stock_{kind}_import.blend'),link=False) as (src,dst):dst.objects=['Armature']
 source=dst.objects[0];bpy.context.scene.collection.objects.link(source);source.hide_render=True
 source_action=source.animation_data.action;start,end=source_action.frame_range;duration=(end-start)/24
 # Meshy animation time is 24 fps in the original import scene.
 source_rest={b.name:b.matrix_local.copy() for b in source.data.bones}
 action=bpy.data.actions.new('Stock_'+kind.title());action.use_fake_user=True;P.arm.animation_data_create();P.arm.animation_data.action=action
 frames=round(duration*48)
 for frame in range(frames+1):
  clock=start+frame/48*24;P.scene.frame_set(int(clock),subframe=clock%1);P.reset()
  for b in source.pose.bones:
   if b.name not in P.REST:continue
   q=b.matrix.to_quaternion()@source_rest[b.name].to_quaternion().inverted()@P.REST[b.name].to_quaternion()
   if b.name=='Hips':
    delta=(b.head-source_rest[b.name].translation)*.01
    P.arm.pose.bones[b.name].matrix=Matrix.Translation(P.REST[b.name].translation+delta)@q.to_matrix().to_4x4();P.update()
   else:P.assign(b.name,q)
  for side in ['Right','Left']:
   suffix='R' if side=='Right' else 'L';fore=P.arm.pose.bones[side+'ForeArm'];delta=fore.matrix.to_quaternion()@P.REST[fore.name].to_quaternion().inverted();P.assign('ForearmTwist.'+suffix,delta@P.REST['ForearmTwist.'+suffix].to_quaternion())
   parent=P.arm.pose.bones[side+'Shoulder'];pd=parent.matrix.to_quaternion()@P.REST[parent.name].to_quaternion().inverted();ld=P.arm.pose.bones[side+'Arm'].matrix.to_quaternion()@P.REST[side+'Arm'].to_quaternion().inverted();P.assign('ArmorShoulder.'+suffix,pd@Quaternion().slerp(pd.inverted()@ld,.28)@P.REST['ArmorShoulder.'+suffix].to_quaternion())
  P.skirt_follow()
  for b in P.arm.pose.bones:
   q=b.rotation_quaternion.copy()
   if frame and q.dot(previous[b.name])<0:q.negate();b.rotation_quaternion=q
   b.keyframe_insert('location',frame=frame+1,group=b.name);b.keyframe_insert('rotation_quaternion',frame=frame+1,group=b.name)
  previous={b.name:b.rotation_quaternion.copy() for b in P.arm.pose.bones}
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
 report.append({'name':action.name,'duration_seconds':frames/48,'frames':frames,'source_action':source_action.name,'source_frame_range':[start,end],'role':'diagnostic only'})
 bpy.data.objects.remove(source,do_unlink=True)
P.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P.OUT/'work/stock_probes_v1.blend'))
(P.OUT/'review/stock_probes.json').write_text(json.dumps(report,indent=2)+'\n')
