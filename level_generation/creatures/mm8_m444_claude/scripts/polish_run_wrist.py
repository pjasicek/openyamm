"""Cap the free left run wrist at 59 degrees; preserve its source twist and all other bones."""
from pathlib import Path
import bpy,sys,math,json
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Running'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];pb=rig.pose.bones['B_L_Hand'];poses=[];maximum=0
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);q=pb.rotation_quaternion.copy();swing,twist=armik.split_swing_twist(q,Vector((0,1,0)));angle=swing.angle
 if angle>math.pi:angle=2*math.pi-angle;swing.negate()
 reduction=max(0,angle-math.radians(59));maximum=max(maximum,math.degrees(reduction))
 if reduction:q=Quaternion(swing.axis,angle-reduction)@Quaternion((0,1,0),twist)
 poses.append(q)
for f,q in enumerate(poses):pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v6.blend'))
maximum=max(maximum,json.loads((p/'work/run_wrist_polish.json').read_text()).get('maximum_correction_degrees',0)) if (p/'work/run_wrist_polish.json').exists() else maximum
(p/'work/run_wrist_polish.json').write_text(json.dumps({'maximum_correction_degrees':maximum,'limit_degrees':59},indent=2));print('RUN_WRIST_POLISH',maximum)
