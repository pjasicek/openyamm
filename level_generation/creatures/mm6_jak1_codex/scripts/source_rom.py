"""G1 ROM of selected motions on the source-frame mannequin, including Mixamo adaptations."""
import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;report={};poses=[]
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']:
 ac=bpy.data.actions[{'Attack':'Staff2','Cast':'Cast1','Death':'StaffFall'}.get(role,role)];rig.animation_data.action=ac
 if len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
 series={b.name:[] for b in rig.pose.bones}
 for f in range(int(ac.frame_range[0]),int(ac.frame_range[1])+1):
  scene.frame_set(f)
  for pb in rig.pose.bones:
   q=pb.matrix_basis.to_quaternion();ang=math.degrees(q.angle);series[pb.name].append((min(ang,360-ang),f))
 report[role]={n:{'max_rotation_deg':max(v)[0],'frame':max(v)[1]} for n,v in series.items()}
 for f in sorted({r['frame'] for n,r in report[role].items() if any(k in n for k in ['Arm','Forearm','Hand','Spine','Clavicle'])}):poses.append({'role':role,'frame':f})
(P/'work/rom.json').write_text(json.dumps({'roles':report,'stress_poses':poses,'source':'round2_sources.blend; StaffAttack2 / StaffCastLAttack1 / StaffDeath1, 30 fps'},indent=2))
assert set(report)=={'Standing','Walking','Attack','Cast','Hit','Death','Fidget'}
print('ROM',len(poses),'stress poses')
