import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/repaired.blend'));r=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene,True)
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name!='Body'
for role,f in [('Attack',42),('Attack',22),('Death',45),('Dead',0)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);common.render_views(str(P/f'review/round4/detail_{role}_{f}'),.85,2.1,views=('front','left','three_quarter'),resolution=(600,750))
