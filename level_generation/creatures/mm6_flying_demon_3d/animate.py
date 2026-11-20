"""Fit airborne source poses on the retained bind using fixed-length chains."""
from pathlib import Path
import bpy, json, math, numpy as np
from mathutils import Matrix, Quaternion, Vector

P=Path(__file__).resolve().parent

def update(): bpy.context.view_layer.update()
def rotate(bone,q):
 pivot=bone.head.copy();bone.matrix=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)@bone.matrix;update()
def assign(bone,q,point):
 matrix=q.to_matrix().to_4x4();matrix.translation=point;bone.matrix=matrix;update()
def sample(rows,t,loop=False):
 t=min(max(t,0),len(rows)-1);i=min(int(t),len(rows)-2);u=t-i
 p0=np.array(rows[(i-1)% (len(rows)-1)] if loop and i==0 else rows[max(0,i-1)])
 p1=np.array(rows[i]);p2=np.array(rows[i+1])
 p3=np.array(rows[(i+2)%(len(rows)-1)] if loop and i+2>=len(rows) else rows[min(len(rows)-1,i+2)])
 return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)
def basis(direction,normal):
 direction=direction.normalized();normal=(normal-direction*normal.dot(direction)).normalized();width=direction.cross(normal).normalized()
 return Matrix((width,direction,normal)).transposed()
def solve_chain(side,parts,target,hint):
 upper,lower,end=[rig.pose.bones['mixamorig:'+side+p] for p in parts]
 a=lower.bone.head_local-upper.bone.head_local;b=end.bone.head_local-lower.bone.head_local
 origin=upper.head.copy();delta=target-origin;distance=delta.length
 assert abs(a.length-b.length)<distance<a.length+b.length,(side,parts,float(distance),a.length+b.length,scene.frame_current)
 axis=delta.normalized();pole=(hint-axis*hint.dot(axis)).normalized()
 along=(a.length_squared-b.length_squared+distance*distance)/(2*distance)
 elbow=origin+axis*along+pole*math.sqrt(max(0,a.length_squared-along*along))
 assign(upper,a.rotation_difference(elbow-origin)@upper.bone.matrix_local.to_quaternion(),origin)
 assign(lower,b.rotation_difference(target-elbow)@lower.bone.matrix_local.to_quaternion(),elbow)
 return upper,lower,end,elbow

flight_wings=[[12,44,0],[4,0,0],[-7,3,48],[-9,12,64],[-2,24,48],[9,42,15],[12,44,0]]
right_attack=[[-.34,-.37,.76],[-.47,-.42,.79],[-.68,-.35,1.01],[-.60,-.40,.96],[.055,-.62,1.17],[-.29,-.49,.77],[-.34,-.37,.76]]
left_attack=[[.32,-.38,.79],[.38,-.40,.80],[.61,-.36,.94],[.29,-.45,1.23],[.30,-.43,.86],[.34,-.40,.77],[.32,-.38,.79]]
right_dirs=[[.10,-.15,-1],[.03,-.22,-1],[-1,-.20,-.12],[-1,-.25,-.45],[1,-.10,-.28],[.15,-.20,-1],[.10,-.15,-1]]
left_dirs=[[-.12,-.15,-1],[-.15,-.2,-1],[1,-.10,-.20],[.4,-.25,.8],[-.4,-.2,-1],[-.12,-.15,-1],[-.12,-.15,-1]]
right_hit=[[-.34,-.37,.76],[-.57,-.36,1.08],[-.63,-.32,1.43],[-.60,-.34,1.31],[-.50,-.34,.95],[-.34,-.38,.80],[-.34,-.37,.76]]
left_hit=[[.32,-.38,.79],[.54,-.34,1.10],[.59,-.29,1.49],[.55,-.32,1.30],[.43,-.35,.99],[.32,-.38,.80],[.32,-.38,.79]]
hit_directions=[[.1,-.15,-1],[.6,-.1,.2],[.5,-.2,.85],[.6,-.2,.7],[.3,-.1,-.6],[.1,-.15,-1],[.1,-.15,-1]]
roll_history={};quaternion_history={};hand_anchor_data={};last_hand_pose={}

def pose(clip,frame):
 phase=frame/6;t=frame/48;loop=clip=='Flight'
 if clip=='Ash_Remains': phase=0;t=0
 if clip=='Death': phase=min(phase,3.8)
 for bone in rig.pose.bones: bone.matrix_basis=Matrix.Identity(4)
 update()
 bob=float(sample([0,.013,.025,.013,-.007,-.014,0],phase,True))
 root=rig.pose.bones['mixamorig:Hips'];m=root.matrix.copy();m.translation.z+=.12+bob;root.matrix=m;update()
 yaw=0;bank=0;lean=6
 if clip=='Attack':
  yaw=float(sample([0,-7,-18,-11,18,4,0],phase));bank=float(sample([0,2,7,3,-5,1,0],phase));lean=float(sample([6,7,9,13,10,6,6],phase))
 if clip in ('Hit','Death'):
  yaw=float(sample([0,3,8,4,1,0,0],phase));bank=float(sample([0,-3,-11,-7,-2,0,0],phase));lean=float(sample([6,-2,-13,-6,3,6,6],phase))
 rotate(rig.pose.bones['mixamorig:Spine'],Quaternion((1,0,0),math.radians(lean*.45)))
 rotate(rig.pose.bones['mixamorig:Spine2'],Quaternion((0,0,1),math.radians(yaw))@Quaternion((0,1,0),math.radians(bank))@Quaternion((1,0,0),math.radians(lean*.55)))
 rotate(rig.pose.bones['mixamorig:Head'],Quaternion((0,0,1),math.radians(-yaw*.6))@Quaternion((1,0,0),math.radians(-3)))
 if clip in ('Hit','Death'): rotate(rig.pose.bones['mixamorig:Head'],Quaternion((1,0,0),math.radians(float(sample([0,-6,-18,-12,-3,0,0],phase)))))
 rotate(rig.pose.bones['Bone_025'],Quaternion((1,0,0),math.radians(4+(float(sample([0,2,6,11,8,2,0],phase)) if clip=='Attack' else 0))))
 for side,sign in [('Left',1),('Right',-1)]:
  ankle=Vector((sign*.15,-.165+(sign*.012),.345+bob+sign*.007))
  if clip=='Attack': ankle+=Vector((sign*.014*math.sin(t*math.pi/.75),.025*math.sin(t*math.pi/.75),.014*math.sin(t*2*math.pi/.75)))
  if clip in ('Hit','Death'):
   kick=float(sample([0,.1,1,.65,.1,0,0],phase))
   ankle+=Vector((sign*(.075 if side=='Left' else .14)*kick,.06*kick,(.28 if side=='Left' else .09)*kick))
  _,_,foot,knee=solve_chain(side,('UpLeg','Leg','Foot'),ankle,Vector((sign*.15,-1,.08)))
  foot_pitch=38
  if clip in ('Hit','Death'):
   foot_pitch=float(sample([38,10,-65,-28,22,38,38] if side=='Left' else [38,22,-18,0,32,38,38],phase))
  assign(foot,Quaternion((1,0,0),math.radians(foot_pitch))@foot.bone.matrix_local.to_quaternion(),ankle)
  target=Vector((sign*(.33+sign*-.01),-.38,.895+sign*.015+bob))
  direction=Vector((-sign*.12,-.15,-1))
  if clip=='Attack': target=Vector(sample(left_attack if side=='Left' else right_attack,phase));target.z+=.12+bob;direction=Vector(sample(left_dirs if side=='Left' else right_dirs,phase))
  if clip in ('Hit','Death'):
   rows=[list(v) for v in (left_hit if side=='Left' else right_hit)]
   if clip=='Death':
    rows[3]=[.40,-.39,.80] if side=='Left' else [-.42,-.37,.78]
    rows[4]=rows[0][:]
   target=Vector(sample(rows,phase));target.z+=.12+bob
   direction=Vector(sample(hit_directions,phase));direction.x*=sign
  upper,lower,hand,elbow=solve_chain(side,('Arm','ForeArm','Hand'),target,Vector((sign*.55,.7,-.4)))
  bases=[rig.data.bones['mixamorig:'+side+'Hand'+d+'1'].head_local for d in ('Index','Middle','Pinky','Ring')]
  rest_long=sum(bases,Vector())/4-hand.bone.head_local;rest_width=bases[-1]-bases[0];rest_normal=rest_width.cross(rest_long).normalized()
  if side=='Left': rest_normal.negate()
  axis=(target-elbow).normalized();profile=hand_anchor_data.get((clip,side))
  if profile:
   roll=float(sample(profile['roll'],phase,loop))
  else:
   # Solve anatomical palm frames at source anchors, where their direction is
   # observed. Interpolate forearm roll and LOCAL wrist rotations afterwards:
   # recomputing shortest swing/twist every frame flips near antipodal axes.
   bend=axis.rotation_difference(direction.normalized())
   if bend.angle>math.radians(65): direction=Quaternion().slerp(bend,math.radians(65)/bend.angle)@axis
   desired=(basis(direction,Vector((0,-1,.13)))@basis(rest_long,rest_normal).transposed()@hand.bone.matrix_local.to_3x3()).to_quaternion()
   difference=desired@hand.matrix.to_quaternion().inverted()
   if difference.w<0:difference.negate()
   roll=2*math.atan2(Vector((difference.x,difference.y,difference.z)).dot(axis),difference.w)
   previous=roll_history.get(side,roll)
   roll+=round((previous-roll)/(2*math.pi))*2*math.pi;roll_history[side]=roll
  rotate(lower,Quaternion(axis,roll))
  for i,fraction in enumerate((0,1/3,2/3)): rotate(rig.pose.bones[f'Demon_{side}_ForearmTwist{i}'],Quaternion(axis,-roll*(1-fraction)))
  if profile:
   hand.rotation_mode='QUATERNION';hand.rotation_quaternion=Quaternion(sample(profile['wrist'],phase,loop));hand.rotation_quaternion.normalize();update()
  else:assign(hand,desired,target)
  last_hand_pose[side]=(roll,hand.matrix_basis.to_quaternion())
  curl=float(sample([0,-12,-16,-10,10,2,0] if side=='Right' else [0,1,-9,-11,3,1,0],phase)) if clip=='Attack' else 0
  for digit in ('Index','Middle','Pinky','Ring'):
   for joint,factor in [(1,.35),(2,.8),(3,1)]:
    bone=rig.pose.bones[f'mixamorig:{side}Hand{digit}{joint}'];bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion((1,0,0),math.radians(curl*factor))
  flap,fold,pitch=sample(flight_wings,phase,True)
  if clip=='Attack': flap,fold,pitch=sample([[12,44,0],[4,6,0],[-8,5,45],[-9,14,60],[2,22,42],[8,38,15],[12,44,0]],phase)
  if clip in ('Hit','Death'):
   bank_side=('Right' if side=='Left' else 'Left') if clip in ('Hit','Death') else side
   flap,fold,pitch=sample([[12,44,0],[7,8,5],[16 if bank_side=='Left' else -38,8 if bank_side=='Left' else 30,15],([-38,10,15] if clip=='Death' else [4,13,45]),[1,22,40],[9,40,12],[12,44,0]],phase)
  rotate(rig.pose.bones[f'Wing_{side}_Root'],Quaternion((0,1,0),math.radians(-sign*flap))@Quaternion((0,0,1),math.radians(sign*fold))@Quaternion((1,0,0),math.radians(-pitch)))
  # Distal wing fingers fold slightly on recovery; the membranes deform with them.
  for i in range(4):
   rotate(rig.pose.bones[f'Wing_{side}_Finger{i+1}'],Quaternion((0,0,1),math.radians(sign*(i*.5)*pitch/65)))
 update()
 for bone in rig.pose.bones:
  assert max(abs(s-1) for s in bone.scale)<1e-5,(bone.name,'scale',tuple(bone.scale))
  if bone.name!='mixamorig:Hips': assert bone.location.length<2e-5,(bone.name,'translation',tuple(bone.location))

def main(input_path,output_path,pilot=True):
 global scene,rig
 bpy.ops.wm.open_mainfile(filepath=str(input_path))
 scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
 scene.render.fps=48
 rig.animation_data_clear()
 for o in scene.objects:
  if o.get('material_role')=='body':
   for face in o.data.polygons: face.use_smooth=True
 
 hand_anchor_data.clear()
 for clip,end in [('Flight',36),('Attack',36),('Hit',36),('Death',42),('Ash_Remains',6)]:
  roll_history.clear();rows={side:{'roll':[],'wrist':[]} for side in ('Left','Right')}
  for frame in range(0,end+1,6):
   scene.frame_set(frame);pose(clip,frame)
   for side in rows:
    roll,q=last_hand_pose[side];row=rows[side]
    if row['wrist'] and q.dot(Quaternion(row['wrist'][-1]))<0:q.negate()
    row['roll'].append(roll);row['wrist'].append(tuple(q))
  for side in rows:hand_anchor_data[(clip,side)]=rows[side]
 for clip,end in [('Flight',36),('Attack',36),('Hit',36),('Death',42),('Ash_Remains',6)]:
  rig.animation_data_create();action=bpy.data.actions.new(clip);rig.animation_data.action=action
  roll_history.clear();quaternion_history.clear()
  for frame in range(end+1):
   scene.frame_set(frame);pose(clip,frame)
   for bone in rig.pose.bones:
    bone.rotation_mode='QUATERNION';q=bone.rotation_quaternion
    if bone.name in quaternion_history and q.dot(quaternion_history[bone.name])<0: q.negate()
    quaternion_history[bone.name]=q.copy()
    for channel in ('location','rotation_quaternion','scale'): bone.keyframe_insert(channel,frame=frame,group=bone.name)
  for curve in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
   for key in curve.keyframe_points: key.interpolation='LINEAR'
  rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=clip;track.strips.new(clip,0,action)
  for t in rig.animation_data.nla_tracks: t.mute=True
  print('Authored',clip,end+1,'fixed-chain samples',flush=True)
 def activate(clip,frame):
  for o in scene.objects:
   for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
    if owner and owner.animation_data:
     owner.animation_data.action=None
     for t in owner.animation_data.nla_tracks: t.mute=t.name!=clip
  scene.frame_set(frame);update()
 
 activate('Flight',0);scene.frame_start=0;scene.frame_end=36
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(output_path),compress=True)
 if not pilot: return
 # Fixed cameras and ordinary lighting provide material-independent pilot evidence.
 scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=720;scene.render.resolution_y=720
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.world.color=(.13,.13,.13)
 scene.eevee.taa_render_samples=32
 camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=3.1
 for name,pos,power in [('Fly_Key',(-3,-4,5),500),('Fly_Fill',(3,1,3),300)]:
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=4
  light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=pos
  light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
 for clip,frames in [('Flight',[0,12,24]),('Attack',[12,18,24])]:
  for frame in frames:
   activate(clip,frame)
   for view,pos in [('front',(0,-6,1.20)),('profile',(6,0,1.20))]:
    camera.location=pos;camera.rotation_euler=(Vector((0,0,1.12))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(P/'review'/f'pilot_{clip}_{frame:02d}_{view}.png');bpy.ops.render.render(write_still=True)
 print('Saved and rendered flight/attack pilot.',flush=True)

if __name__=='__main__': main(P/'work/anatomy_wings.blend',P/'work/animations.blend')
