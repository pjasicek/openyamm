import sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import bpy,common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v8.blend'));r=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene)
for role,f in [('Standing',0),('Walking',10),('Attack',23),('Death',23),('Death',54)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 common.render_views(str(p/f'review/strain_{role}_{f}'),.85,2.15,views=('front','back','left'),resolution=(500,600))
