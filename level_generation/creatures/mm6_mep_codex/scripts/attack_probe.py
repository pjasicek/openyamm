import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/geometry_final.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];common.workbench_clay(bpy.context.scene,True)
for f in [7,20,28,34.375,40]:
 bpy.context.scene.frame_set(int(f),subframe=f%1)
 print('ATTACK',f,{n:list(r.pose.bones[n].head) for n in ['B_Pelvis','B_R_UpperArm','B_R_Forearm','B_R_Hand']},flush=True)
 common.render_views(str(p/f'review/contact_attack_{f}'),.85,2.2,views=('front','left'),resolution=(600,700))
