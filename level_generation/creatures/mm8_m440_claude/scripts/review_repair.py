from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from club import add_club
club=add_club(rig);common.workbench_clay(sc)
for name,f in [('Fidget',20),('Fidget',32),('Running',12),('Death',20)]:
 rig.animation_data.action=bpy.data.actions[name];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(f);club.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
 common.render_views(str(p/'review'/f'repaired_{name}_{f}'),1.,2.4,views=('front','left','back'),resolution=(480,600))
 if name=='Fidget':
  H=rig.matrix_world@rig.pose.bones['B_Head'].matrix;common.render_views(str(p/'review'/f'repaired_head_{f}'),H.translation.z,.65,views=('front','left','back'),resolution=(600,600),target=(H.translation.x,H.translation.y))
