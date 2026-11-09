import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import numpy as np
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01/upright_audit';src=next(s for s in reversed(list(bpy.data.scenes)) if s.name.startswith('Goblin - Repaired Rig Review'));oldarm=next(o for o in src.objects if o.type=='ARMATURE');oldmesh=max((o for o in src.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
s=bpy.data.scenes.new('Goblin - Posture Alignment v2');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24
reference=oldarm.copy();reference.data=oldarm.data.copy();reference.name='Posture_PreviousRig_Reference';s.collection.objects.link(reference)
for t in reference.animation_data.nla_tracks:t.mute=True
arm=oldarm.copy();arm.data=oldarm.data.copy();arm.name='MM6_Goblin_Upright_Rig';s.collection.objects.link(arm);arm.animation_data_clear();arm.animation_data_create()
mesh=oldmesh.copy();mesh.data=oldmesh.data.copy();mesh.name='MM6_Goblin_Upright_10577';s.collection.objects.link(mesh);mat=oldmesh.matrix_world.copy();mesh.parent=arm;mesh.matrix_world=mat
for m in mesh.modifiers:
 if m.type=='ARMATURE':m.object=arm
for o in src.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
s.camera.location=(0,-5,.85);s.camera.rotation_euler=(Vector((0,0,.85))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=2.15
source_actions={k:bpy.data.actions['Goblin_Fixed_'+k] for k in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose']}
report=json.loads((OUT/'posture_report.json').read_text());angle=math.radians(sum(report['clips'][k]['stats']['lateral_lean_deg']['mean'] for k in ['Idle_3','Walking'])/2)
qs={side:[] for side in ['Left','Right']}
for key in ['Idle_3','Walking']:
 a=source_actions[key];reference.animation_data.action=a;reference.animation_data.action_slot=a.slots[0]
 for i in range(48):
  f=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/48;s.frame_set(int(f),subframe=f-int(f))
  for side in qs:qs[side].append(list(reference.pose.bones['mixamorig:'+side+'Shoulder'].matrix_basis.to_quaternion()))
def mean(qs):
 a=np.array(qs);a[a@a[0]<0]*=-1;return Quaternion(tuple(np.mean(a,axis=0))).normalized()
shoulders={side:mean(q) for side,q in qs.items()};alignment={'torso_lateral_bias_degrees':math.degrees(angle),'shoulder_neutral_correction_degrees':{k:math.degrees(q.angle) for k,q in shoulders.items()},'method':'Constant torso alignment about pelvis in the heading frame; shoulder neutral rotation offsets from idle/walk. Original cyclic variation retained.'};(OUT/'alignment_v2.json').write_text(json.dumps(alignment,indent=2))
jobs=list(source_actions);actions={};render_jobs=[]
def step():
 try:
  bpy.context.window.scene=s
  if jobs:
   key=jobs.pop(0);a=source_actions[key];reference.animation_data.action=a;reference.animation_data.action_slot=a.slots[0];new=a.copy();new.name='Goblin_Upright_'+key;actions[key]=new;arm.animation_data.action=new;arm.animation_data.action_slot=new.slots[0];prevq=None
   for f in range(math.floor(a.frame_range[0]),math.ceil(a.frame_range[1])+1):
    s.frame_set(f)
    if key=='restpose':continue
    hips=reference.pose.bones['mixamorig:Hips'];spine=reference.pose.bones['mixamorig:Spine'];delta=hips.matrix@hips.bone.matrix_local.inverted();right=delta.to_quaternion()@Vector((1,0,0));right.z=0;right.normalize();forward=Vector((right.y,-right.x,0));q=Quaternion(forward,angle);origin=hips.head;rotate=Matrix.Translation(origin)@q.to_matrix().to_4x4()@Matrix.Translation(-origin);desired=rotate@spine.matrix;bone=arm.data.bones['mixamorig:Spine'];basis=bone.matrix_local.inverted()@hips.bone.matrix_local@hips.matrix.inverted()@desired;pb=arm.pose.bones[bone.name];qb=basis.to_quaternion()
    if prevq:qb.make_compatible(prevq)
    prevq=qb.copy();pb.rotation_quaternion=qb;pb.location=basis.translation;pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=bone.name);pb.keyframe_insert(data_path='location',frame=f,group=bone.name)
    for side,offset in shoulders.items():
     name='mixamorig:'+side+'Shoulder';q0=reference.pose.bones[name].matrix_basis.to_quaternion();arm.pose.bones[name].rotation_quaternion=q0@offset.inverted();arm.pose.bones[name].keyframe_insert(data_path='rotation_quaternion',frame=f,group=name)
   for layer in new.layers:
    for strip in layer.strips:
     bag=strip.channelbag(new.slots[0])
     if bag:
      for fc in bag.fcurves:
       for kp in fc.keyframe_points:kp.interpolation='LINEAR'
   new.use_fake_user=True
   if key in ['Idle_3','Walking','Running']:
    render_jobs.append((key,new,new.frame_range[0]+.25*(new.frame_range[1]-new.frame_range[0])))
   return .1
  if render_jobs:
   name,a,f=render_jobs.pop(0);arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];arm.data.pose_position='POSE';s.frame_set(int(f),subframe=f-int(f));s.render.filepath=str(OUT/('upright_'+name+'.png'));bpy.ops.render.render(write_still=True);return .1
  arm.data.pose_position='REST';s.render.filepath=str(OUT/'neutral_rest.png');bpy.ops.render.render(write_still=True);arm.data.pose_position='POSE';reference.hide_set(True);reference.hide_render=True
  for key,a in actions.items():
   track=arm.animation_data.nla_tracks.new();track.name=key;strip=track.strips.new(key,int(a.frame_range[0]),a);strip.action_slot=a.slots[0];track.mute=True
  arm.animation_data.action=actions['Walking'];arm.animation_data.action_slot=actions['Walking'].slots[0];s.frame_start=1;s.frame_end=26;s.frame_set(7);bpy.data.libraries.write(str(OUT/'posture_v2_working.blend'),{s},fake_user=True,compress=True);(OUT/'v2_done.txt').write_text('complete');return None
 except Exception:(OUT/'v2_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(alignment))
