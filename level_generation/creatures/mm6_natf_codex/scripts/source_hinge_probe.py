import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_actions.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;report={}
for name in ['Standing','Walking','Attack','Cast','Hit']:
 ac=bpy.data.actions[name];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];report[name]={}
 for sd in 'LR':
  rows=[]
  for f in np.linspace(0,ac.frame_range[1],5):
   sc.frame_set(int(f),subframe=float(f%1));a,b,c=[rig.pose.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head-a.head).normalized();v=(c.head-b.head).normalized();h=a.matrix.to_3x3().inverted()@u.cross(v).normalized();rows.append({'f':float(f),'axis_local':list(h),'flex':math.degrees(u.angle(v))})
  report[name][sd]=rows
print(json.dumps(report,indent=1));(P/'work/source_hinge_probe.json').write_text(json.dumps(report,indent=2))
