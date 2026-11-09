import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import numpy as np
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01';oldscene=bpy.data.scenes['Goblin - Meshy Rig Diagnosis'];srcarm=next(o for o in oldscene.objects if o.type=='ARMATURE');weights_scene=bpy.data.scenes['Goblin - Local Rig Repair'];oldmesh=weights_scene.objects['Goblin_RepairedWeights']
s=bpy.data.scenes.new('Goblin - Centered Rig and Retarget');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=oldscene.world;s.view_settings.view_transform='AgX';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24
source=srcarm.copy();source.data=srcarm.data.copy();source.name='Goblin_Retarget_Source';s.collection.objects.link(source);source.data.pose_position='POSE'
for t in source.animation_data.nla_tracks:t.mute=True
for o in oldscene.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
mesh=oldmesh.copy();mesh.data=oldmesh.data.copy();mesh.name='Goblin_CenteredRig_Mesh';s.collection.objects.link(mesh);matrix=oldmesh.matrix_world.copy();mesh.parent=None;mesh.matrix_world=matrix
# Correct garment inner-surface membership; these UVs lie on y=0.5 in the atlas.
uv=mesh.data.uv_layers.active.data;garment=set()
for p in mesh.data.polygons:
 if any(uv[i].uv.x>.49999 or uv[i].uv.y>.49999 for i in p.loop_indices):garment.update(p.vertices)
for i in garment:
 v=mesh.data.vertices[i];p=mesh.matrix_world@v.co;t=min(.4,max(0,(.973-p.z)/.24*.4)) if p.z<.973 else 0;side='Left' if p.x>0 else 'Right'
 for g in list(v.groups):mesh.vertex_groups[g.group].remove([i])
 mesh.vertex_groups['mixamorig:Hips'].add([i],1-t,'REPLACE')
 if t:mesh.vertex_groups['mixamorig:'+side+'UpLeg'].add([i],t,'REPLACE')
# All disconnected render vertices at the same position must share the same weights.
by_pos={}
for v in mesh.data.vertices:by_pos.setdefault(tuple(round(c,5) for c in v.co),[]).append(v)
for verts in by_pos.values():
 if len(verts)<2:continue
 avg={}
 for v in verts:
  for g in v.groups:avg[g.group]=avg.get(g.group,0)+g.weight/len(verts)
 avg=dict(sorted(avg.items(),key=lambda a:-a[1])[:4]);total=sum(avg.values())
 for v in verts:
  for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
  for i,w in avg.items():mesh.vertex_groups[i].add([v.index],w/total,'REPLACE')
armdata=bpy.data.armatures.new('Goblin_Centered_Armature');arm=bpy.data.objects.new('Goblin_Centered_Rig',armdata);s.collection.objects.link(arm);bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
heads={b.name:source.matrix_world@b.head_local for b in source.data.bones}
for key,xyz in {'Hips':(0,.005,.92923),'Spine':(0,.005,1.04),'Spine1':(0,.005,1.20),'Spine2':(0,.005,1.34),'Neck':(0,.005,1.405),'Head':(0,.005,1.50),'HeadTop_End':(0,.005,1.685),'LeftShoulder':(.087,.0,1.35),'RightShoulder':(-.087,.0,1.35),'LeftToeBase':(.13,-.085,.04),'RightToeBase':(-.13,-.085,.04),'LeftToe_End':(.13,-.165,.04),'RightToe_End':(-.13,-.165,.04)}.items():heads['mixamorig:'+key]=Vector(xyz)
heads['headfront']=Vector((0,-.145,1.54))
nextbone={'Hips':'Spine','Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head','Head':'HeadTop_End'}
for side in ['Left','Right']:
 for a,b in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('Hand','HandMiddle4'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase'),('ToeBase','Toe_End')]:nextbone[side+a]=side+b
for b in source.data.bones:
 e=armdata.edit_bones.new(b.name);e.head=heads[b.name];short=b.name.split(':')[-1];key=nextbone.get(short)
 e.tail=heads['mixamorig:'+key] if key else e.head+Vector((0,0,.05));e.align_roll(Vector((0,1,0)))
 if b.parent:e.parent=armdata.edit_bones[b.parent.name]
 e.use_deform=not(short.endswith('End') or short.endswith('Middle4') or short=='headfront')
bpy.ops.object.mode_set(mode='OBJECT');mesh.parent=arm;mesh.matrix_world=matrix
for m in mesh.modifiers:
 if m.type=='ARMATURE':m.object=arm;m.use_deform_preserve_volume=False
arm.animation_data_create();names=[b.name for b in arm.data.bones];bind={b.name:b.matrix_local.copy() for b in arm.data.bones};source_bind={b.name:(source.matrix_world@b.matrix_local).copy() for b in source.data.bones}
def src_delta(name):return (source.matrix_world@source.pose.bones[name].matrix@source_bind[name].inverted()).to_quaternion().normalized()
def meanquat(qs):
 a=np.array([list(q) for q in qs]);a[a@a[0]<0]*=-1;return Quaternion(tuple(np.mean(a,axis=0))).normalized()
# Neutral idle supplies a constant retarget alignment correction, not frame-by-frame motion cancellation.
a=bpy.data.actions['Idle_3'];source.animation_data.action=a;source.animation_data.action_slot=a.slots[0];headqs=[];footqs={'Left':[],'Right':[]}
for t in [0,.25,.5,.75,1]:
 f=a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0]);s.frame_set(int(f),subframe=f-int(f));headqs.append(src_delta('mixamorig:Spine2').inverted()@src_delta('mixamorig:Head'))
 for side in footqs:footqs[side].append(src_delta('mixamorig:'+side+'Foot'))
head_offset=meanquat(headqs);feet_offset={side:meanquat(qs) for side,qs in footqs.items()}
report={'head_alignment_offset_degrees':head_offset.angle*180/math.pi,'foot_alignment_offsets_degrees':{k:v.angle*180/math.pi for k,v in feet_offset.items()},'garment_vertices':len(garment),'bones':[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local)} for b in arm.data.bones],'actions':[]}
actions={};jobs=['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose'];render_jobs=[]
def step():
 try:
  bpy.context.window.scene=s
  if jobs:
   key=jobs.pop(0);(OUT/'retarget_progress.txt').write_text('retarget '+key);src=bpy.data.actions[key];source.animation_data.action=src;source.animation_data.action_slot=src.slots[0];act=bpy.data.actions.new('Goblin_Fixed_'+key);arm.animation_data.action=act
   for f in range(math.floor(src.frame_range[0]),math.ceil(src.frame_range[1])+1):
    s.frame_set(f);q={name:src_delta(name) for name in names}
    if key!='restpose':
     q['mixamorig:Head']=q['mixamorig:Spine2']@(q['mixamorig:Spine2'].inverted()@q['mixamorig:Head'])@head_offset.inverted()
     q['mixamorig:Neck']=q['mixamorig:Spine2'].slerp(q['mixamorig:Head'],.5)
     for side in feet_offset:
      q['mixamorig:'+side+'Foot']=q['mixamorig:'+side+'Foot']@feet_offset[side].inverted();q['mixamorig:'+side+'ToeBase']=q['mixamorig:'+side+'Foot']
    desired={}
    for name in names:
     bone=arm.data.bones[name];pb=arm.pose.bones[name];base=bind[name];parent=bone.parent
     parent_matrix=desired[parent.name] if parent else Matrix.Identity(4);rest_relative=bind[parent.name].inverted()@base if parent else base
     location=(parent_matrix@rest_relative).translation
     if not parent:
      location=base.translation+(source.matrix_world@source.pose.bones[name].head-source_bind[name].translation)
     rot=q[name]@base.to_quaternion();pose=rot.to_matrix().to_4x4();pose.translation=location;desired[name]=pose
     basis=base.inverted()@(bind[parent.name]@parent_matrix.inverted() if parent else Matrix.Identity(4))@pose
     pb.rotation_mode='QUATERNION';pb.rotation_quaternion=basis.to_quaternion();pb.location=basis.translation;pb.scale=(1,1,1);pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=name)
     if not parent:pb.keyframe_insert(data_path='location',frame=f,group=name)
   act.use_fake_user=True;actions[key]=act;report['actions'].append({'source':key,'output':act.name,'range':list(act.frame_range)})
   if key in ['Idle_3','Walking','Right_Hand_Sword_Slash']:
    for t in [.25,.6]:render_jobs.append((key+'_'+str(t),act,src.frame_range[0]+t*(src.frame_range[1]-src.frame_range[0])))
   return .1
  if render_jobs:
   key,a,f=render_jobs.pop(0);arm.animation_data.action=a
   if a.slots:arm.animation_data.action_slot=a.slots[0]
   s.frame_set(int(f),subframe=f-int(f));s.render.filepath=str(OUT/('centered_'+key+'.png'));bpy.ops.render.render(write_still=True);return .1
  source.hide_set(True);source.hide_render=True;(OUT/'retarget_report.json').write_text(json.dumps(report,indent=2));bpy.data.libraries.write(str(OUT/'centered_rig.blend'),{s},fake_user=True,compress=True);(OUT/'retarget_done.txt').write_text('complete');return None
 except Exception:(OUT/'retarget_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Centered skeleton and corrected motion alignment scheduled.')
