import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
common.workbench_clay(sc);common.render_views(str(p/'review/round2/sleeve_clay'),1.2,1.05,views=('front','left','three_quarter'),resolution=(700,700))
