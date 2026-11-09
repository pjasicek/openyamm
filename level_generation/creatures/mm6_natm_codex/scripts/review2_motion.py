"""Repair the existing library clips and neck weights; preserve round-1 cloth/feather work."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
SOURCE=P/'work/review_round2_before/work'
config=json.loads((P/'gates.json').read_text());palm=Vector(config['hands']['L']['palm_axis']);receipt={'method':'World-space counter-rotation; constant local neck/head offsets. Existing library torso/leg motion retained.', 'clips':{},'neck_weights':{}}
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def bags(action):
 for layer in action.layers:
  for strip in layer.strips:
   for slot in action.slots:
    bag=strip.channelbag(slot)
    if bag:yield bag
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'runtime_lod{level}.blend'));C.reset();r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];skin=body.data.attributes['piece'].data
 count=0
 for v in body.data.vertices:
  if skin[v.index].value!=0 or v.co.z<1.36:continue
  z=v.co.z;mix=smooth(1.36,1.435,z)*(1-smooth(.075,.15,abs(v.co.x)))
  if z>=1.49:mix=1
  if mix<=0:continue
  old={body.vertex_groups[g.group].name:g.weight for g in v.groups};head=smooth(1.455,1.525,z);neck=(1-head)*smooth(1.365,1.445,z);new={'B_Spine2':1-head-neck,'B_Neck':neck,'B_Head':head}
  final={n:old.get(n,0)*(1-mix)+new.get(n,0)*mix for n in set(old)|set(new)};total=sum(final.values());assert abs(total-1)<1e-4
  for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
  for n,w in final.items():
   if w>1e-7:body.vertex_groups[n].add([v.index],w/total,'REPLACE')
  count+=1
 receipt['neck_weights'][str(level)]=count
 for a in list(bpy.data.actions):
  snapshots=[];end=int(a.frame_range[1]);C.activate(a.name,0); head_angles=[]
  for frame in range(end+1):
   bpy.context.scene.frame_set(frame);snapshots.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
  r.animation_data.action=None
  corrected=[];angles=[]
  for frame,snapshot in enumerate(snapshots):
   for b in r.pose.bones:b.matrix_basis=snapshot[b.name]
   bpy.context.view_layer.update()
   if a.name not in ['Death','Dead']:
    spine=r.pose.bones['B_Spine2'];delta=(spine.matrix.to_3x3()@spine.bone.matrix_local.to_3x3().inverted()).to_quaternion()
    for n,share in [('B_Neck',.22),('B_Head',.035)]:
     b=r.pose.bones[n];goal=Quaternion().slerp(delta,share)@b.bone.matrix_local.to_quaternion();m=goal.to_matrix().to_4x4();m.translation=b.head;b.matrix=m;b.location=(0,0,0);b.scale=(1,1,1);bpy.context.view_layer.update()
   # Turn the casting arm toward the victim, then present the open palm without replacing the source gesture.
   if a.name=='Cast':
    amount=smooth(4,23,frame)*(1-smooth(38,68,frame));b=r.pose.bones['B_L_UpperArm'];m=b.matrix.copy();m=Matrix.Rotation(math.radians(-30)*amount,4,'X')@Matrix.Rotation(math.radians(-12)*amount,4,'Z')@m;m.translation=b.head;b.matrix=m;bpy.context.view_layer.update()
    h=r.pose.bones['B_L_Hand'];normal=(h.matrix.to_3x3()@palm).normalized();goal=Vector((0,-.89100652,-.45399050));q=Quaternion().slerp(normal.rotation_difference(goal),amount);m=(q@h.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=h.head;h.matrix=m;h.location=snapshot[h.name].to_translation();h.scale=(1,1,1);bpy.context.view_layer.update()
    # Recompute only the two existing left twist helpers after changing the arm/wrist.
    for base,child,helper,factor in [('Forearm','Hand','ForearmTwist',.6),('UpperArm','Forearm','UpperArmTwist',-.5)]:
     pb=r.pose.bones['B_L_'+base];cb=r.pose.bones['B_L_'+child];axis=(pb.bone.matrix_local.inverted()@cb.bone.head_local).normalized()
     dq=(pb.matrix.inverted()@cb.matrix).to_quaternion()@(pb.bone.matrix_local.inverted()@cb.bone.matrix_local).to_quaternion().inverted() if base=='Forearm'else pb.matrix_basis.to_quaternion()
     tw=(2*math.atan2(Vector((dq.x,dq.y,dq.z)).dot(axis),dq.w)+math.pi)%(2*math.pi)-math.pi;r.pose.bones['B_L_'+helper].rotation_quaternion=Quaternion(axis,tw*factor)
    bpy.context.view_layer.update();angles.append(math.degrees((h.matrix.to_3x3()@palm).angle(Vector((0,-1,0)))))
   for n in ['B_Neck','B_Head']:
    r.pose.bones[n].location=(0,0,0);r.pose.bones[n].scale=(1,1,1)
   bpy.context.view_layer.update()
   head=r.pose.bones['B_Head'];forward=head.matrix.to_3x3()@head.bone.matrix_local.to_3x3().inverted()@Vector((0,-1,0));head_angles.append(math.degrees(forward.angle(Vector((0,-1,0)))))
   corrected.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in ['B_Neck','B_Head']+(['B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_UpperArmTwist','B_L_ForearmTwist']if a.name=='Cast'else[])})
  if a.name=='Cast':
   for iteration in range(2):
    old=[{n:q.copy()for n,q in row.items()}for row in corrected]
    for frame in range(1,len(corrected)-1):
     for n in ['B_L_UpperArm','B_L_Hand','B_L_UpperArmTwist','B_L_ForearmTwist']:corrected[frame][n]=old[frame-1][n].slerp(old[frame+1][n],.5).slerp(old[frame][n],.5)
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  for bag in bags(a):
   for fc in list(bag.fcurves):
    if any(fc.data_path==f'pose.bones["{n}"].{prop}'for n in ['B_Neck','B_Head']for prop in ['location','scale']):bag.fcurves.remove(fc)
  previous={}
  for frame,pose in enumerate(corrected):
   for n,q in pose.items():
    if n in previous and previous[n].dot(q)<0:q.negate()
    previous[n]=q.copy();b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=frame,group=n)
  for bag in bags(a):
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
  if level==0:
   receipt['clips'][a.name]={'frames':end,'neck_head_translation_scale_curves':0}
   receipt['clips'][a.name]['authored_head_forward_max_deg']=max(head_angles)
   if a.name in ['Attack','Cast']:assert max(head_angles)<20
   if angles:receipt['clips'][a.name]['cast_palm_at_frame_23_deg']=angles[23];assert angles[23]<30
  print('MOTION',level,a.name,flush=True)
 C.reset();r.location=(0,0,0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
(P/'review/round2_motion.json').write_text(json.dumps(receipt,indent=2))
