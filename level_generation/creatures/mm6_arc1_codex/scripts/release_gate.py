import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_authoring.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
for tick in range(53*4):
 f=tick/4;sc.frame_set(int(f),subframe=f-int(f));bm=rig.pose.bones['Bow'].matrix;n=rig.pose.bones['BowNock'].head;local=bm.inverted()@n;rows.append({'frame':f,'draw_m':local.y-.187,'arrow_scale':rig.pose.bones['Arrow'].scale.x})
sc.frame_set(36);direction=rig.pose.bones['Arrow'].matrix.to_3x3().col[2].normalized();socket=rig.pose.bones['Socket_Arrow_Release'].head;rest=rig.pose.bones['Bow'].matrix@Vector((0,0,.085));nock=rig.pose.bones['BowNock'].head
angle=math.degrees(direction.angle(Vector((0,-1,0))));error=(socket-(rest+direction*.08)).length
speeds=[((b['draw_m']-a['draw_m'])*120,a['frame'],b['frame'])for a,b in zip(rows,rows[1:])];speed,f0,f1=min(speeds)
assert angle<8 and error<1e-5,(angle,error)
assert 35.75<=f0<=37.25,(speed,f0,f1)
assert rows[144]['arrow_scale']>.99 and rows[148]['arrow_scale']<.002
out={'release_seconds':1.2,'release_frame_30fps':36,'arrow_axis_degrees_from_forward':angle,'arrow_axis':list(direction),'launch_socket_offset_error_m':error,'launch_socket_world_m':list(socket),'nock_world_m':list(nock),'peak_string_contraction_m_per_s':-speed,'peak_string_contraction_frame_interval':[f0,f1],'last_full_arrow_seconds':1.2,'first_hidden_arrow_seconds':37/30,'grip_contact_report':'round3/contact_gates.json','blade_edge_gate':'not applicable: no blade; measured arrow axis and string release instead','string':'skinned 24-triangle moving string; rigid wooden limbs'}
(P/'review/release_gate.json').write_text(json.dumps(out,indent=2));print('RELEASE',out)

for clip in ['Attack','Cast']:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 distances=[]
 for frame in range(26,37):
  sc.frame_set(frame);distances.append((rig.pose.bones['BowNock'].head-rig.pose.bones['B_R_Finger1'].head).length)
 assert max(distances)<1e-4,(clip,distances)
 out[clip+'_draw_nock_knuckle_distance_m']=max(distances)
(P/'review/release_gate.json').write_text(json.dumps(out,indent=2))
