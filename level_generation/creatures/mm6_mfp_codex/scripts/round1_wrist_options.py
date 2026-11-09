import bpy,sys,math
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/lod0.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];fb=r.data.bones['B_R_Forearm'];hb=r.data.bones['B_R_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
for ob in list(sc.objects):
 if ob not in [r,b,k]:bpy.data.objects.remove(ob,do_unlink=True)
common.workbench_clay(sc,True);sc.display.shading.light='FLAT'
for sign in [-1,1]:
 for f in [10,12.5,16]:
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f%1);r.animation_data.action=None
  r.pose.bones['B_R_Forearm'].rotation_quaternion@=Quaternion(axis,math.radians(sign*44));r.pose.bones['B_R_Hand'].rotation_quaternion=Quaternion(Vector((0,1,0)),math.radians(sign*44));r.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(axis,math.radians(sign*26.4));bpy.context.view_layer.update()
  common.render_views(str(P/f'review/round1/wrist{sign}_{f:g}'),1.12,1.4,views=('three_quarter',),resolution=(520,700))
