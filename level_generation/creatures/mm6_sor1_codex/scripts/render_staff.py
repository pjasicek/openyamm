import bpy,sys,json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/production_master.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];staff=bpy.data.objects['Staff']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
for o in scene.objects:
 if o.type=='MESH' and o!=staff:o.hide_render=True
common.workbench_clay(scene,textured=True)
lo,hi=common.world_bounds([staff]);centre=(lo+hi)/2
common.render_views(str(p/'review/staff_full'),centre.z,1.95,views=('front','three_quarter'),resolution=(420,1000),target=(centre.x,centre.y))
tip=rig.matrix_world@rig.pose.bones['Socket_Staff_Head'].head
common.render_views(str(p/'review/staff_crown'),tip.z-.04,.28,views=('front','three_quarter'),resolution=(650,650),target=(tip.x,tip.y))
data=json.loads(scene['staff']);bone=rig.pose.bones['B_Staff'];grip=rig.matrix_world@bone.head
common.render_views(str(p/'review/staff_grip'),grip.z,.30,views=('front','three_quarter'),resolution=(650,650),target=(grip.x,grip.y))
