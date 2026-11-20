"""Keep the selected punch's extension but point its striking arm toward the actor's target."""
from pathlib import Path
import sys,bpy,math,json,numpy as np
from mathutils import Matrix,Vector
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
act=bpy.data.actions['Attack'];rig.animation_data.action=act
if act.slots:rig.animation_data.action_slot=act.slots[0]
rows=[]
for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
 sc.frame_set(f)
 for s in 'LR':
  sh=rig.pose.bones['B_'+s+'_UpperArm'].head;wr=rig.pose.bones['B_'+s+'_Hand'].head
  d=wr-sh;rows.append((d.length,f,s,d.copy()))
length,impact,side,d=max(rows,key=lambda x:x[0]);yaw=-math.atan2(d.x,-d.y)
poses=[]
for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
 sc.frame_set(f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 # A smooth correction around the actual extension, fading during recovery.
 t=min(1.,max(0.,f/max(impact-2,1)),max(0.,(23-f)/max(23-impact-2,1)));t=t*t*(3-2*t)
 pb=rig.pose.bones['B_'+side+'_UpperArm'];M=pb.matrix.copy();pos=M.translation.copy();M=Matrix.Rotation(yaw*t,4,'Z')@M;M.translation=pos;pb.matrix=M;bpy.context.view_layer.update()
 # Keep the gaze toward the blow while its arm changes azimuth.
 head=rig.pose.bones['B_Head'];M=head.matrix.copy();pos=M.translation.copy();M=Matrix.Rotation(yaw*t*.75,4,'Z')@M;M.translation=pos;head.matrix=M;bpy.context.view_layer.update()
 poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ('B_'+side+'_UpperArm','B_Head')});rig.animation_data.action=act
for f,pose in enumerate(poses):
 for n,q in pose.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
sc.frame_set(impact);d=rig.pose.bones['B_'+side+'_Hand'].head-rig.pose.bones['B_'+side+'_UpperArm'].head
assert abs(d.x)<.01 and d.y<-.3,d[:]
p=Path(__file__).resolve().parents[1];(p/'review/punch_aim.json').write_text(json.dumps({'side':side,'source_extension_frame':impact,'extension_m':length,'azimuth_correction_degrees':math.degrees(yaw),'corrected_direction':list(d),'note':'Arm azimuth adaptation over selected Mixamo punch; source extension speed preserved.'},indent=2)+'\n')
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
