import bpy,json,math
from pathlib import Path
s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];vals={n:[] for n in ['mixamorig:RightForeArm','mixamorig:RightHand']}
for f in [1+i*.5 for i in range(37)]:
 s.frame_set(int(f),subframe=f-int(f))
 for name in vals:
  q=r.pose.bones[name].rotation_quaternion;angle=math.degrees(2*math.atan2(q.y,q.w))
  if vals[name]:angle+=360*round((vals[name][-1][1]-angle)/360)
  vals[name].append([f,angle])
out={k:{'min':min(a[1] for a in v),'max':max(a[1] for a in v),'values':v} for k,v in vals.items()};Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01/twist_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:{x:y for x,y in v.items() if x!='values'} for k,v in out.items()}));s.frame_set(4)
