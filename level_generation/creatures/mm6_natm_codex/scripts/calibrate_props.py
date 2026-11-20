"""Calibrate the spear's shaft to the orthographic native side view; preserve its grip and blade."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/weight_fit.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear();tip=height*119/254;butt=height*110/254;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
M=rig.data.bones['Spear'].matrix_local;inv=M.inverted();ob=bpy.data.objects['SpearMesh']
for v in ob.data.vertices:
 p=inv@v.co;z=p.z
 if z>.775:p.z=z+tip-1.08
 elif z>.15:p.z=.15+(z-.15)*(tip-.305-.15)/(.775-.15)
 elif z<-.15:p.z=-.15+(z+.15)*(butt-.15)/(.89-.15)
 v.co=M@p
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones['Socket_SpearTip'];delta=M.to_3x3()@Vector((0,0,tip-1.08));b.head+=delta;b.tail+=delta;bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/contact_master.blend'));(P/'review/calibration.json').write_text(json.dumps({'native_side_frame':'../mm6_natm/native/natmsta2.png','native_body_height_px':254,'native_spear_grip_to_tip_px':119,'native_spear_grip_to_butt_px':110,'body_height_m':height,'spear_tip_m':tip,'spear_butt_m':butt,'spear_length_m':tip+butt,'native_visible_height_units':254*.699997,'actor_scale':254*.699997/height,'grip_and_blade_preserved':True},indent=2));print('CALIBRATION',height,tip,butt,flush=True)
