"""Contact-fit the authored motion, level the fitted boots and size the grip to the measured fist."""
import bpy,json,math
import numpy as np
from mathutils import Matrix,Vector,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_finished.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
# The measured grip gaps were 2.3--4.5 mm: a 13.6 mm grip brings all fingertips into the 3 mm band.
sword=bpy.data.objects['CutlassMesh'];sb=rig.data.bones['Sword'].matrix_local;inv=sb.inverted();changed=0
for v in sword.data.vertices:
 local=inv@v.co;rad=math.hypot(local.x,local.z)
 if .0105<rad<.0121 and -.058<local.y<.074:
  local.x*=.0136/.012;local.z*=.0136/.012;v.co=sb@local;changed+=1
assert changed>=60
st=bpy.data.actions['Standing'];rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];sc.frame_set(0)
feet={side:(rig.pose.bones[f'B_{side}_Foot'].matrix.to_3x3().inverted()@rig.data.bones[f'B_{side}_Foot'].matrix_local.to_3x3()) for side in 'LR'}
acts=[a for a in bpy.data.actions if a.name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']]
report={}
for act in acts:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];times=np.arange(0,float(act.frame_range[1])+.001,.25);frames=[]
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1))
  # Small shoulder clearance for the thick shirt and rigid hook cuff, in the torso frame.
  for side,sign in [('R',1),('L',-1)]:
   degrees=0 if act.name=='Running' else (5 if side=='R' else 8)
   if act.name=='Fidget' and side=='R':degrees=10
   name=f'B_{side}_UpperArm';mat=rig.pose.bones[name].matrix.copy();head=mat.translation.copy()
   axis=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,1,0))).normalized()
   mat=Matrix.Rotation(math.radians(sign*degrees),4,axis)@mat;mat.translation=head;rig.pose.bones[name].matrix=mat;bpy.context.view_layer.update()
  for side in 'LR':
   fn,hn=f'B_{side}_Forearm',f'B_{side}_Hand';fb,hb=rig.data.bones[fn],rig.data.bones[hn];axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fn].matrix.inverted()@rig.pose.bones[hn].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();dq=rel@rest.inverted()
   tw=(2*math.atan2(Vector((dq.x,dq.y,dq.z)).dot(axis),dq.w)+math.pi)%(2*math.pi)-math.pi
   limit=math.radians(90);wanted=tw
   if abs(tw)>limit:wanted=math.copysign(limit+math.radians(20)*math.tanh((abs(tw)-limit)/math.radians(20)),tw)
   mat=rig.pose.bones[hn].matrix.copy();head=mat.translation.copy();wa=rig.pose.bones[fn].matrix.to_3x3()@axis
   mat=Matrix.Rotation(wanted-tw,4,wa)@mat;mat.translation=head;rig.pose.bones[hn].matrix=mat
   rig.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*wanted)
   bpy.context.view_layer.update()
   foot=rig.pose.bones[f'B_{side}_Foot'];mat=foot.matrix.copy();R=mat.to_3x3()@feet[side];new=R.to_4x4();new.translation=mat.translation;foot.matrix=new
   rig.pose.bones[f'B_{side}_Toe0'].matrix_basis.identity();bpy.context.view_layer.update()
  frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
 # Remove tiny source cycle-end drift gradually, instead of adding a discontinuity at the loop.
 if act.name in ['Standing','Walking','Running']:
  last=frames[-1]
  for i,pose in enumerate(frames):
   t=i/(len(frames)-1)
   for n,(q,l) in list(pose.items()):
    q0,l0=frames[0][n];q1,l1=last[n];pose[n]=(q@Quaternion().slerp(q1.rotation_difference(q0),t),l+(l0-l1)*t)
 name=act.name;bpy.data.actions.remove(act);out=bpy.data.actions.new(name);out.use_fake_user=True;rig.animation_data.action=out
 for f,pose in zip(times,frames):
  for n,(q,l) in pose.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=float(f))
 out.use_frame_range=True;out.frame_start=0;out.frame_end=float(times[-1])
 # Recalculate ground contact after reorienting the boot soles.
 pv=np.array([a.value for a in body.data.attributes['piece'].data]);footmask=np.isin(pv,[5,6]);rows=[]
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();z=np.array([v.co.z for v in em.vertices]);ev.to_mesh_clear();low=z.min() if name=='Death' else z[footmask].min()
  dz=max(0,.004-low) if name=='Running' else .004-low
  rows.append((rig.pose.bones['B_Pelvis'].location.copy(),dz))
 invroot=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
 for f,(loc,dz) in zip(times,rows):
  rig.pose.bones['B_Pelvis'].location=loc+invroot@Vector((0,0,float(dz)));rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=float(f))
 for layer in out.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'floor_correction_m':[float(min(d for _,d in rows)),float(max(d for _,d in rows))]}
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_contacts.blend'))
(P/'review/contact_repairs.json').write_text(json.dumps({'grip_vertices':changed,'motion':report},indent=2)+'\n');print('CONTACT_REPAIRS',report)
