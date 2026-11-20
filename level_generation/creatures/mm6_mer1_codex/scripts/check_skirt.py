import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
for n in ['elbow_gate.py','audit_motion.py']:
 sys.argv=[n,'--','work/skirt_v1.blend','skirt_v1'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
import common
r=bpy.data.objects['Rig'];s=bpy.context.scene;common.workbench_clay(s)
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for i in range(5):
  f=a.frame_range[1]*i/4;s.frame_set(int(f),subframe=f%1);common.render_views(str(P/'review'/f'skirt_v1_{name}_{i}'),.85,2.05,views=('front','left','three_quarter'),resolution=(300,450))
