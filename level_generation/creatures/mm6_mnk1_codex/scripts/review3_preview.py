import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
for name,f,z,scale in [('Attack',21.5,1.2,1.1),('Standing',0,1.2,1.1),('Walking',22.5,.5,1.2),('Death',13.125,.6,1.7),('Death',60,.5,2.2)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f%1);common.render_views(str(p/f'review/round3/{name}_{f}'),z,scale,views=('front','left','three_quarter'),resolution=(700,700))
