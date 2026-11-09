import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,False)
for name,frames in [('Standing',[0]),('Walking',[6]),('Death',[0,8,16,24,35,55])]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(f)
  common.render_views(str(p/f'review/feedback_20261011/{name}_{f}'),.65,1.9,views=('left','three_quarter'),resolution=(480,600))
