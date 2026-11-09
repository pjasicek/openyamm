import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_gripped.blend'))
r=bpy.data.objects['Rig'];g=json.loads((P/'work/grip_pose.json').read_text());data={}
for name in ['Attack','Cast','Death']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);m=r.pose.bones['B_R_Hand'].matrix;c=m@Vector(g['handle_centre_hand_local']);d=m.to_3x3()@Vector(g['handle_axis_hand_local']);tip=c+d*1.361
  rows.append({'f':f,'grip':list(c),'axis':list(d),'tip':list(tip),'left':list(r.pose.bones['B_L_Hand'].head)})
 data[name]=rows
(P/'work/motion_probe.json').write_text(json.dumps(data,indent=1))
t=np.array([x['tip'] for x in data['Attack']]);sp=np.linalg.norm(np.diff(t,axis=0),axis=1)*30
for i in np.argsort(sp)[-12:]:print('ATTACK',i+0.5,'speed',round(sp[i],2),'forward',round(-data['Attack'][i]['axis'][1],3),'tip',np.round(t[i],3))
