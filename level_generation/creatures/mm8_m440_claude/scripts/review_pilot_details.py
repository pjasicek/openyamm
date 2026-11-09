from pathlib import Path
import bpy,bmesh,json,sys,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_grip.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
from club import add_club
club=add_club(rig);g=json.loads((p/'work/grip_pose.json').read_text());H=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix;center=H@Vector(g['handle_centre_hand_local']);axis=(H.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized();direction=(H.to_3x3()@Vector((0,1,0))).normalized();normal=axis.cross(direction).normalized()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bm=bmesh.new();bm.from_mesh(ev.to_mesh());ev.to_mesh_clear();bm.transform(body.matrix_world);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co-center).length>.22],context='VERTS');me=bpy.data.meshes.new('GripDetail');bm.to_mesh(me);bm.free();detail=bpy.data.objects.new('GripDetail',me);sc.collection.objects.link(detail);body.hide_render=True
common.workbench_clay(sc)
for name,d in [('axis',axis),('palm',normal),('back',-normal),('tips',direction)]:
 cam=common.ortho_camera(name,center+d, (0,0,0),.43);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=640;sc.render.filepath=str(p/'review'/('actual_grip_'+name+'.png'));bpy.ops.render.render(write_still=True)
body.hide_render=False;detail.hide_render=True
for name,frame in [('Attack',17),('Attack',26),('Attack',38),('Walking',30)]:
 rig.animation_data.action=bpy.data.actions[name];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(frame);club.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
 common.render_views(str(p/'review'/f'pilot_detail_{name}_{frame}'),1.1,2.7,views=('front','three_quarter','back'),resolution=(640,800))
