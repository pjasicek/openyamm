import runpy,sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
for n in ['apply_materials.py','close_sleeve_roots.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
import common
s=bpy.context.scene;r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(0);common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False
common.render_views(str(P/'review/closed_sleeves'),.86,1.92,views=('front','left','three_quarter'),resolution=(600,800))
