import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_candidate.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard'
D=P/'review/round2/candidate';D.mkdir(exist_ok=True,parents=True)
for nm in ['Death','Attack']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for i in range(9):
  f=a.frame_range[1]*i/8;sc.frame_set(int(f),subframe=f%1);common.render_views(str(D/f'{nm}_{i}'),.8,3.6,views=['left','three_quarter'],resolution=(360,360),target=(0,.2))
