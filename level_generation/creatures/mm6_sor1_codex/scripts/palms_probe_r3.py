import bpy,json,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
report={}
for label,file in [('earlier','round3_motion_parallel_grip.blend'),('current','round3_motion.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/file));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(144);G=json.loads((p/'work/grip_pose.json').read_text());H=rig.pose.bones['B_R_Hand'].matrix;A=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();v=[];rad=[]
 for sd,end in [('R','Right'),('L','Left')]:
  socket=rig.pose.bones['Socket_Palm_'+end];n=(socket.tail-socket.head).normalized();v.append((n-A*n.dot(A)).normalized());C=(H@Vector(G['handle_centre_hand_local']))+(A*.5 if sd=='L' else Vector());r=socket.head-C;rad.append((r-A*r.dot(A)).normalized())
 report[label]={'palm_normal_dot':v[0].dot(v[1]),'palm_radial_dot':rad[0].dot(rad[1]),'normals':[list(x) for x in v],'radials':[list(x) for x in rad]}
 common.workbench_clay(scene,textured=True);common.render_views(str(p/'review/round3'/f'{label}_grip'),1.35,.8,views=('front','left'),target=(-.2,-.3),resolution=(640,640))
print('ACTUAL_PALMS',json.dumps(report),flush=True);(p/'work/actual_palms_r3.json').write_text(json.dumps(report,indent=2))
