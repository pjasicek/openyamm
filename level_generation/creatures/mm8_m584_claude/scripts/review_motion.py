from pathlib import Path
import bpy,sys,json
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.5,.5,.5)
out=P/'review/animation_clay';out.mkdir(exist_ok=True)
for name in ('Standing','Walking','Attack','Hit','Death'):
 a=bpy.data.actions.get(name)
 if not a:continue
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 for i in range(7):
  f=a.frame_range[1]*i/6;sc.frame_set(int(f),subframe=f-int(f))
  common.render_views(str(out/f'{name}_{i}'),1.0,4.3,views=('front','left','three_quarter'),resolution=(640,480))
 print('FINAL JOINTS',{n:list(rig.pose.bones[n].head) for n in ('B_Pelvis','B_Head','B_L_UpperArm','B_R_UpperArm','B_L_Hand','B_R_Hand','B_L_Thigh','B_R_Thigh','B_L_Foot','B_R_Foot')},flush=True)
