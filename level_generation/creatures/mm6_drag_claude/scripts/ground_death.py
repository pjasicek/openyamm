import bpy,math,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'));import posing
bpy.ops.wm.open_mainfile(filepath=str(P/'review/reduction/step_01.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()};names=[g.name for g in body.vertex_groups];dom=np.array([names[max(v.groups,key=lambda g:g.weight).group] for v in body.data.vertices]);torso=np.isin(dom,['Root','Spine1','Spine2'])
def coords():
 ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh();a=np.array([v.co[:] for v in me.vertices]);ob.to_mesh_clear();return a
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def corrected(clip,frame):
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);blend=1 if clip=='Dead' else smooth((frame/24-.44)/.43)
 if blend:
  co=coords();rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,(.008-co[torso,2].min())*blend));bpy.context.view_layer.update()
  for side in ['L','R']:
   for upper,lower,end,z in [('Thigh','Shin','Foot',.047),('UpperArm','ForeArm','Hand',.035)]:
    pb=rig.pose.bones[side+end];target=pb.head.copy();target.z=target.z*(1-blend)+z*blend;root=rig.pose.bones[side+upper].head.copy();pole=root+Vector((-.10 if upper=='Thigh' else .10,-.3,.15));q=pb.matrix.to_quaternion();direction=q@Vector((0,1,0));flat=Vector((direction.x,direction.y,0)).normalized();correction=direction.rotation_difference(flat);q=Matrix.LocRotScale(Vector(),correction,Vector((1,1,1))).to_quaternion().slerp(Matrix.Identity(3).to_quaternion(),1-blend)@q
    posing.two_bone_ik(rig,side+upper,side+lower,target,pole);pb.matrix=Matrix.LocRotScale(pb.head.copy(),q,Vector((1,1,1)));bpy.context.view_layer.update()
  low=coords()[:,2].min();rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,-low));bpy.context.view_layer.update()
 return {pb.name:(pb.location.copy(),pb.rotation_quaternion.copy(),pb.scale.copy()) for pb in rig.pose.bones}
poses={k:[corrected(k,f) for f in range(25)] for k in ['Death','Dead']}
for clip,samples in poses.items():
 old=bpy.data.actions[clip];old.name=clip+'_pre_ground';old.use_fake_user=False;action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data.action=action
 for f,pose in enumerate(samples):
  for name,(loc,rot,scale) in pose.items():
   pb=rig.pose.bones[name];pb.location=loc;pb.rotation_quaternion=rot;pb.scale=scale
   for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(channel,frame=f)
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 bpy.data.actions.remove(old)
report={}
for k in ['Death','Dead']:
 rig.animation_data.action=bpy.data.actions[k];report[k]=[]
 for f in range(25):
  sc.frame_set(f);co=coords();report[k].append({'frame':f,'minimum_z':float(co[:,2].min()),'torso_minimum_z':float(co[torso,2].min())})
(P/'review/death_grounding.json').write_text(json.dumps(report,indent=2));rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/death_grounded.blend'))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.6,.63,.6);sc.display.shading.show_cavity=True;sc.render.resolution_x=1000;sc.render.resolution_y=700;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5;target=Vector((.3,-.1,.2));cam.location=target+Vector((2,-5,2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();rig.animation_data.action=bpy.data.actions['Dead'];sc.frame_set(0);sc.render.filepath=str(P/'review/dead_grounded.png');bpy.ops.render.render(write_still=True)
print('GROUNDED',report['Dead'][0])
