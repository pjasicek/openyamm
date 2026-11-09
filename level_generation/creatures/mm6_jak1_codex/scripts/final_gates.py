import bpy,runpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));roles=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('posture.py',[]);run('uv_gate.py',[]);run('batch_pose_audit.py',[]);run('grip_floor_audit.py',[])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));bpy.data.objects['Jackalman'].name='Body';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_gate_master.blend'))
run('g4_weights.py',[P/'work/final_gate_master.blend','final',*[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,max(1,bpy.context.scene.render.fps//48))]])
run('g5_hand_stretch.py',[P/'work/final_gate_master.blend',*roles]);run('g6_head_clearance.py',[P/'work/final_gate_master.blend',*roles]);run('g6_staff_mesh.py',[P/'export/mm6_jak1_runtime_lod0.glb'])
L=P.parents[2]/'anim_library/humanoid_set'
run('trace_export.py',[P/'export/mm6_jak1_runtime_lod0.glb',f'Walking={L}/Armed.glb:ArmedWalk',f'Hit={L}/Unarmed.glb:UnarmedGetHitF1',f'Attack={L}/2Hand Staff.glb:StaffAttack2',f'Cast={L}/2Hand Staff.glb:StaffCastLAttack1',f'Death={L}/2Hand Staff.glb:StaffDeath1'])
run('blow_gate.py',[])
for name in ['g6_contacts.py','g6_skirt_poke.py']:run(name,[P/'work/final_gate_master.blend',*roles])
run('source_rom.py',[]);run('round2_motion_metrics.py',[]);run('shared_bone_audit.py',[])

g4=json.loads((P/'work/g4_final.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text())
assert max(v['stretch_p99']for ss in g4.values()for v in ss.values())<=2.0
assert max(v['max_edge_stretch']for ss in g5.values()for v in ss.values())<=4.5
for name in ['g6_staff_mesh','g6_fauld']:
 data=json.loads((P/f'work/{name}.json').read_text());assert max(v['depth_m']for v in data.values())<=.002,(name,data)
data=json.loads((P/'work/g6_contacts.json').read_text());assert all(v[0]<=.2 for d in data.values()for k,v in d.items()if k!='max_clear_blade_m'),data
assert all(not v['flags']for v in json.loads((P/'work/g6_trace.json').read_text()).values())
assert all(v['depth_m']<=.01 for v in json.loads((P/'work/g6_head.json').read_text()).values())
for sides in json.loads((P/'review/batch_pose_audit.json').read_text()).values():
 for row in sides.values():
  assert row['flex_min_deg']>=-5 and row['plane_error_max_deg']<1
  assert row['forearm_roll_max_deg']<=90.001 and row['helper_roll_max_deg']<=90.001
for clip in ['Standing','Fidget']:
 for row in json.loads((P/'review/batch_pose_audit.json').read_text())[clip].values():
  assert row['heel_toe_max_delta_m']<=.01 and max(row['heel_max_m'],row['toe_max_m'])<=.01,(clip,row)
for row in json.loads((P/'review/grip_floor.json').read_text()).values():
 assert row['body_min_z_m']>=-.0001 and row['staff_min_z_m']>=-.0001 and (row['grip_min_skin_radius_m'] is None or row['grip_min_skin_radius_m']>=.0126),row
audit=json.loads((P/'review/batch_pose_audit.json').read_text())
for clip,sides in audit.items():
 for side,row in sides.items():
  assert row['upper_roll_max_deg']<=60.1,(clip,side,row)
  assert row['palm_to_shaft_min_dot'] is None or row['palm_to_shaft_min_dot']>.8,(clip,side,row)
  if clip in ['Standing','Fidget']:
   assert row['sole_tilt_max_deg']<=3 and row['palm_to_body_min_dot']>.8,(clip,side,row)
  if clip=='Walking':
   if side=='L':assert row['palm_to_body_min_dot']>.8,(clip,side,row)
   assert row['toe_yaw_max_deg']<=10 and .08<=row['swing_peak_m']<=.12 and 40<=row['knee_at_swing_peak_deg']<=61,(clip,side,row)
grip=json.loads((P/'review/round2/two_hand_grip.json').read_text());assert grip['max_relative_rotation_deg']<=1;assert grip['max_offaxis_m']<=.003 and max(abs(x-.29)for x in grip['span_range_m'])<=.003
assert json.loads((P/'review/grip_floor.json').read_text())['Attack']['offhand_min_skin_radius_m']>=.0126
assert json.loads((P/'review/grip_floor.json').read_text())['Dead']['corpse_max_z_m']<=.45
accel=json.loads((P/'review/round2/angular_acceleration.json').read_text())
assert not any(accel['over_threshold'].values()),accel['over_threshold']
import hashlib
receipt={'status':'pass','glb_sha256':hashlib.sha256((P/'export/mm6_jak1_runtime_lod0.glb').read_bytes()).hexdigest(),'sample_hz':48,'angular_acceleration_max_deg_s2':max(r['max_deg_s2']for rows in accel['runtime'].values()for r in rows.values()),'triangles':json.loads((P/'export/export_info.json').read_text())['triangles']}
(P/'review/round2/rig_gate_receipt.json').write_text(json.dumps(receipt,indent=2))
print('ALL RIG GATES PASS',receipt,flush=True)
