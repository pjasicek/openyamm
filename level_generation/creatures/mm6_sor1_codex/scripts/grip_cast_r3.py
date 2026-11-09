import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];samples=[]
for file in ['review/round3/baseline/work/production_master.blend','work/round3_motion.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(p/file));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 a=bpy.data.actions['Cast'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for t in np.arange(0,2.05,1/48):
  f=t*120;scene.frame_set(int(f),subframe=float(f%1));rows.append([np.array(pb.matrix) for pb in rig.pose.bones])
 samples.append(np.array(rows))
error=float(abs(samples[0]-samples[1]).max());assert error<1e-6,error
G=json.loads((p/'work/grip_pose.json').read_text());L=json.loads((p/'work/round2_left_grip.json').read_text());act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
for t in np.arange(.9,1.575,1/48):
 f=t*120;scene.frame_set(int(f),subframe=float(f%1));H=rig.pose.bones['B_R_Hand'].matrix;C=H@Vector(G['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();LH=rig.pose.bones['B_L_Hand'].matrix;LC=LH@Vector(L['centre']);v=[]
 for end in ['Right','Left']:
  socket=rig.pose.bones['Socket_Palm_'+end];normal=(socket.tail-socket.head).normalized();v.append((normal-A*normal.dot(A)).normalized())
 rows.append({'time':float(t),'left_grip_error_mm':(LC-C-A*.5).length*1000,'opposed_palm_normals_dot':v[0].dot(v[1])})
report={'cast_world_matrix_max_change':error,'grip':rows,'max_grip_error_mm':max(r['left_grip_error_mm'] for r in rows),'opposed_palm_normals_dot_range':[min(r['opposed_palm_normals_dot'] for r in rows),max(r['opposed_palm_normals_dot'] for r in rows)]};print('GRIP_AND_CAST',json.dumps(report),flush=True);(p/'work/grip_cast_r3.json').write_text(json.dumps(report,indent=2))

assert report['max_grip_error_mm']<=3 and report['opposed_palm_normals_dot_range'][1]<-.5
