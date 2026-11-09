"""Accept the complete measured authoring master and export the Forge at 60 Hz."""
import bpy,sys,os,json,shutil,runpy,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
read=lambda n:json.loads((P/'review'/n).read_text())
g=read('gates_forge_concept.json');assert len(g)==9
slam=read('forge_slam_gate.json');assert slam['passed'] and g['Forge_Attack']['maul_slam_passed']
assert slam['master_sha256']==hashlib.sha256((P/'work/forge_final_clearance.blend').read_bytes()).hexdigest()
summary={'arm_p99':0,'hand_max':0,'wrist_swing':0,'shell_p99':0,'shell_max':0,'armour_contact_cm':0}
for role,row in g.items():
 for side in 'LR':
  for suffix,limit in [('arm_p99',2.05),('hand_max',4.5),('wrist_swing',60)]:
   v=row[side+'_'+suffix]['value'];assert v<=limit,(role,side,suffix,v);summary[suffix]=max(summary[suffix],v)
  assert row[side+'_hand_in_body']['value']==0
 assert row['body_floor_min']>=-.02
for row in read('shell_stretch_forge_concept.json').values():
 for p99,mx in row.values():
  assert p99<=1.10 and mx<=1.25;summary['shell_p99']=max(summary['shell_p99'],p99);summary['shell_max']=max(summary['shell_max'],mx)
assert not any(read('shell_leak_forge_concept.json').values())
for row in read('armour_gate_forge_concept.json').values():
 for plate in row.values():
  for depth,*_ in plate.values():assert depth<=.30;summary['armour_contact_cm']=max(summary['armour_contact_cm'],depth)
for row in read('equipment_forge_concept.json').values():
 for entry in row.values():assert not entry['head_intersection_frames'] and entry['floor_min_m']>=-.002
src=P/'work/forge_final_clearance.blend';out=P/'work/forge_complete.blend';old=P/'work/review_before_20261023/forge_complete_before_resume.blend'
if out.exists() and not old.exists():shutil.copy2(out,old)
shutil.copy2(src,out);summary.update(slam_impact_s=slam['impact_s'],slam_checks=slam['checks'],passed=True,roles=9,master_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(P/'review/forge_gate_acceptance.json').write_text(json.dumps(summary,indent=2)+'\n');print('FORGE_ACCEPTED',summary,flush=True)
bpy.ops.wm.open_mainfile(filepath=str(out));r=bpy.data.objects['Rig'];sc=bpy.context.scene
C={s:Vector(json.loads((P/f'work/grip_pose_{"R" if s=="R" else "L_tun"}.json').read_text())['handle_centre_hand_local']) for s in 'LR'}
report={};trajectory=[]
for role in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast'):
 a=bpy.data.actions['Forge_'+role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows={s:[] for s in ('R' if role=='Cast' else 'LR')}
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));inv=armik.W(r,'Thunder_Maul').inverted()
  for side in rows:rows[side].append(list(inv@(armik.W(r,f'B_{side}_Hand')@C[side])))
  if role=='Attack':trajectory.append({'time':float(f/30),'impact_socket_z_up':list(armik.W(r,'Socket_Maul_Impact').translation)})
 report[role]={s:{'radial_max_m':float(np.linalg.norm(np.array(v)[:,[0,2]],axis=1).max()),'shaft_range_m':[float(np.min(np.array(v)[:,1])),float(np.max(np.array(v)[:,1]))]} for s,v in rows.items()}
(P/'review/forge_grip_clearance.json').write_text(json.dumps(report,indent=2)+'\n');(P/'review/maul_strike_trajectory_review.json').write_text(json.dumps(trajectory,indent=2)+'\n');print('FORGE_GRIPS',report,flush=True)
sys.argv=['export_lancer.py','--',str(out),'forge'];runpy.run_path(str(S/'export_lancer.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
