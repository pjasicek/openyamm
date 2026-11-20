import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_assembled.blend'));r=bpy.data.objects['Rig'];s=bpy.context.scene
for name,f in [('Death',72),('Attack',39)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(f)
 for b in r.pose.bones:
  if any(b.name.endswith(k) for k in ['Pelvis','Spine','Head','UpperArm','Forearm','Hand','Thigh','Calf','Foot']): print(name,b.name,list(b.head))
 common.workbench_clay(s);common.render_views(str(P/f'review/probe_{name}'),.95,3.0,views=('front','left','three_quarter'),resolution=(420,600))
