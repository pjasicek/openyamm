import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];src=P/'work/forge_slam.blend';bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
names=[b.name for b in r.pose.bones if any(x in b.name for x in ('Hand','UpperArm','Forearm'))];previous={};steps={}
for f in np.arange(0,a.frame_range[1]+.001,.5):
 sc.frame_set(int(f),subframe=float(f%1))
 for n in names:
  q=r.pose.bones[n].matrix_basis.to_quaternion()
  if n in previous:
   deg=math.degrees(previous[n].rotation_difference(q).angle);deg=min(deg,360-deg)
   if deg>steps.get(n,{}).get('degrees',-1):steps[n]={'degrees':deg,'frame':float(f)}
  previous[n]=q.copy()
(P/'review/forge_slam_continuity.json').write_text(json.dumps(steps,indent=2)+'\n');print('STEP_MAXIMA',json.dumps(steps),flush=True);sys.stdout.flush();os._exit(0)
