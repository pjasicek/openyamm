import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01';src=bpy.data.scenes['Goblin - Meshy Rig Diagnosis'];oldarm=next(o for o in src.objects if o.type=='ARMATURE');oldmesh=max((o for o in src.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
s=bpy.data.scenes.new('Goblin - Local Rig Repair');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24
arm=oldarm.copy();arm.data=oldarm.data.copy();arm.name='Goblin_RepairedRig';s.collection.objects.link(arm)
mesh=oldmesh.copy();mesh.data=oldmesh.data.copy();mesh.name='Goblin_RepairedWeights';s.collection.objects.link(mesh);mesh.parent=arm;mesh.matrix_world=oldmesh.matrix_world.copy()
for mod in mesh.modifiers:
 if mod.type=='ARMATURE':mod.object=arm
for o in src.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
for t in arm.animation_data.nla_tracks:t.mute=True
names={g.index:g.name for g in mesh.vertex_groups};groups={g.name:g for g in mesh.vertex_groups};uv=mesh.data.uv_layers.active.data;garment=set()
for p in mesh.data.polygons:
 if any(uv[i].uv.x>.501 or uv[i].uv.y>.501 for i in p.loop_indices):garment.update(p.vertices)
changed={}
def set_weights(v,weights,why):
 total=sum(weights.values())
 for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
 for name,w in weights.items():
  if w>.00001:groups['mixamorig:'+name].add([v.index],w/total,'REPLACE')
 changed[why]=changed.get(why,0)+1

def blend(a,b,t):return {a:1-t,b:t}
for v in mesh.data.vertices:
 p=mesh.matrix_world@v.co;x,y,z=p;side='Left' if x>0 else 'Right'
 if z>=1.48:set_weights(v,{'Head':1},'rigid_head')
 elif abs(x)<.105 and z>1.345:
  if z>1.415:set_weights(v,blend('Neck','Head',min(1,(z-1.415)/.065)),'neck_allowed_bones')
  else:set_weights(v,blend('Spine2','Neck',max(0,(z-1.345)/.07)),'neck_allowed_bones')
 elif v.index in garment:
  if z>.973:set_weights(v,{'Hips':1},'belt_rigid_hips')
  else:
   # A small progressive leg contribution keeps the hanging strips responsive; the belt stays rigid.
   t=min(.4,max(0,(.973-z)/.24*.4));set_weights(v,blend('Hips',side+'UpLeg',t),'skirt_limited_leg_influence')
 elif -.285<x<-.182 and .807<z<.977 and -.105<y<.135:set_weights(v,{'Hips':1},'pouch_hips')
 elif .012<abs(x)<.165 and 1.25<z<1.405 and y>.138:set_weights(v,{'Spine2':1},'backplate_rigid_chest')
 elif z<.125:set_weights(v,{side+'Foot':1},'rigid_foot')
 else:
  w={names[g.group].split(':')[-1]:g.weight for g in v.groups}
  for suffix,target in [('HandMiddle4','Hand'),('Toe_End','Foot')]:
   key=side+suffix
   if key in w:
    w[side+target]=w.get(side+target,0)+w.pop(key);set_weights(v,w,'remove_terminal_bone_weights');break
(OUT/'weight_changes.json').write_text(json.dumps({'vertices_by_operation':changed,'garment_vertices':len(garment),'note':'Position/UV-based local influence cleanup. Bind bones and animation tracks unchanged for controlled comparison.'},indent=2))
jobs=[]
for key in ['Idle_3','Walking','Right_Hand_Sword_Slash']:
 a=bpy.data.actions[key]
 for t in [.25,.6]:jobs.append((key+'_'+str(t),a,a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0])))

def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   bpy.data.libraries.write(str(OUT/'weights_repaired.blend'),{s},fake_user=True,compress=True);(OUT/'weights_done.txt').write_text('complete');return None
  name,a,frame=jobs.pop(0);arm.data.pose_position='POSE';arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(int(frame),subframe=frame-int(frame));s.render.filepath=str(OUT/('weights_'+name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'weights_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(changed))
