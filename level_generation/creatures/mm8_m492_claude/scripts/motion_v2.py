"""Scoped native-informed Attack/Cast and stronger Hit; the user requested a flame-free death."""
import bpy, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion
P=Path(__file__).resolve().parents[1];OUT=P/'review/motion_v2'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_motion_v2/dragon_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
# Seconds, chest dip, neck bend, head nod, head yaw, rearward shift, wing elevation, jaw.
ATTACK=np.array([
 [0,0,0,0,0,0,65,.025],
 [.125,-.02,-.07,.04,.20,.006,61,.10],
 [.25,0,-.03,.02,.36,.012,53,.24],
 [.50,.10,.20,-.12,.24,.035,32,.44],
 [.75,.22,.48,-.62,.06,.065,14,.62],
 [1.00,.26,.64,-.80,-.12,.080,7,.72],
 [1.125,.26,.64,-.80,-.12,.080,8,.72],
 [1.25,.34,.82,-1.02,0,.060,10,.78],
 [1.375,.18,.42,-.52,-.36,.060,24,.50],
 [1.50,.05,.08,-.06,-.24,.025,48,.20],
 [40/24,0,0,0,0,0,65,.025],
])
# Seconds, root backward pitch, lateral bank, root yaw, neck arch, head yaw, head nod, jaw, recoil.
HIT=np.array([
 [0,0,0,0,0,0,0,.025,0],
 [.125,-.20,.14,.08,-.16,.42,-.08,.30,.55],
 [.25,-.32,.28,.15,-.34,.62,-.18,.48,.90],
 [.375,-.38,.36,.17,-.44,.34,-.24,.60,1],
 [.50,-.28,.42,.10,-.28,-.24,-.10,.52,.94],
 [.625,-.08,.34,-.12,.08,-.72,.10,.34,.70],
 [.75,.08,.14,-.20,.26,-.60,-.14,.20,.40],
 [.875,.04,-.06,-.12,.14,-.34,-.08,.10,.18],
 [1.00,-.02,-.04,-.04,.02,-.14,0,.04,.05],
 [1.125,0,0,0,0,0,0,.025,0],
 [1.25,0,0,0,0,0,0,.025,0],
])
def curve(table,t):
 xs=table[:,0];ys=table[:,1:];i=min(len(xs)-2,max(0,int(np.searchsorted(xs,t,side='right')-1)));dt=xs[i+1]-xs[i];u=np.clip((t-xs[i])/dt,0,1)
 slopes=np.zeros_like(ys);slopes[1:-1]=(ys[2:]-ys[:-2])/(xs[2:]-xs[:-2])[:,None]
 return (2*u**3-3*u**2+1)*ys[i]+(u**3-2*u**2+u)*dt*slopes[i]+(-2*u**3+3*u**2)*ys[i+1]+(u**3-u**2)*dt*slopes[i+1]
def rot(n,axis,a):rig.pose.bones[n].rotation_quaternion @= Quaternion(axes[n]@Vector(axis),float(a))
def surface():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return co
# Snapshot the selected flight, so other clips, UVs, weights and materials stay untouched.
base={}
for name,frames in [('Attack',40),('Hit',30)]:
 rig.animation_data.action=bpy.data.actions['Standing']
 for f in range(frames+1):
  sample=f/frames*33;sc.frame_set(int(sample),subframe=sample%1);base[name,f]={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
for name,frames in [('Attack',40),('Cast',40),('Hit',30)]:
 bpy.data.actions.remove(bpy.data.actions[name]);act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act
 for f in range(frames+1):
  t=f/24;phase=math.tau*f/frames
  for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.matrix_basis=base['Attack' if name=='Cast' else name,f][b.name]
  if name in ('Attack','Cast'):
   dip,bend,nod,yaw,back,elevation,jaw=curve(ATTACK,t)
   for spine in ['Spine1','Spine2']:rot(spine,(1,0,0),dip/2)
   for i in range(1,4):rot(f'Neck{i}',(1,0,0),bend/3);rot(f'Neck{i}',(0,0,1),yaw/6)
   rot('Head',(1,0,0),nod);rot('Head',(0,0,1),yaw/2)
   rig.pose.bones['Root'].location+=axes['Root']@Vector((0,back,.009*math.sin(math.pi*f/frames)**2))
   for side,sg in [('L',1),('R',-1)]:
    rot(side+'Wing0',(0,1,0),-sg*(math.radians(elevation)-math.radians(35+30*math.cos(phase))))
    old=.20+.95*max(0,min(1,(math.cos(phase)+.2)/1.2))**2*(3-2*max(0,min(1,(math.cos(phase)+.2)/1.2)))
    feather=.20+.95*max(0,min(1,(elevation-35)/30))
    b=rig.pose.bones[side+'Wing2'];b.rotation_quaternion @= Quaternion((0,1,0),float(sg*(feather-old)))
    rot(side+'ForeUpper',(1,0,0),-.35*dip)
   for i in range(1,11):rot(f'Tail{i}',(0,0,1),-.018*yaw)
  else:
   pitch,bank,turn,bend,yaw,nod,jaw,recoil=curve(HIT,t)
   rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rot('Root',(0,0,1),turn)
   rig.pose.bones['Root'].location+=axes['Root']@Vector((.022*recoil,.045*recoil,.024*recoil))
   for i in range(1,4):rot(f'Neck{i}',(1,0,0),bend/3);rot(f'Neck{i}',(0,0,1),yaw/6)
   rot('Head',(1,0,0),nod);rot('Head',(0,0,1),yaw/2)
   for side,sg in [('L',1),('R',-1)]:
    rot(side+'Wing0',(0,1,0),-.30*recoil)
    rot(side+'ForeUpper',(1,0,0),.30*recoil);rot(side+'ForeLower',(1,0,0),-.20*recoil)
    rot(side+'HindUpper',(1,0,0),.14*recoil)
   for i in range(1,11):rot(f'Tail{i}',(0,0,1),-.055*recoil);rot(f'Tail{i}',(1,0,0),.032*recoil)
  rig.pose.bones['Jaw'].rotation_quaternion=Quaternion(axes['Jaw']@Vector((1,0,0)),float(jaw))
  bpy.context.view_layer.update()
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('scale',frame=f)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
# Keep the selected collapse exactly; disable its fire controls as well as omitting the effect mesh on delivery.
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'MouthFire' in fc.data_path and fc.data_path.endswith('.scale'):
      for key in fc.keyframe_points:key.co.y=1e-6;key.interpolation='CONSTANT'
bpy.data.objects['MouthFire'].hide_render=True
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_v2.blend'))
for o in sc.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/motion_v2_clips.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='NONE',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(OUT/'authored.json').write_text(json.dumps({'attack':ATTACK.tolist(),'hit':HIT.tolist(),'fps':24,'impact':1.25,'death':'selected collapse retained; no flame'},indent=2)+'\n')
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO';sc.render.film_transparent=True;sc.render.resolution_x=600;sc.render.resolution_y=500;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('MotionCamera',bpy.data.cameras.new('MotionCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.05
report={}
for name,ts in [('Attack',[0,.25,.5,.75,1,1.25,1.5]),('Hit',[0,.125,.25,.375,.5,.625,.75,1])]:
 rig.animation_data.action=bpy.data.actions[name];rows=[]
 for i,t in enumerate(ts):
  f=t*24;sc.frame_set(int(f),subframe=f%1);co=surface();mouth=rig.pose.bones['Socket_Mouth'].head
  rows.append({'time':t,'minimum_z':float(co[:,2].min()),'maximum_z':float(co[:,2].max()),'head':list(rig.pose.bones['Head'].head),'mouth':list(mouth),'adult_mouth_horizontal':math.hypot(mouth.x,mouth.y)*1504.288787,'small_mouth_z':mouth.z*1203.43103})
  for view,delta in [('front',(0,-3,.05)),('right',(3,0,.05)),('quarter',(2,-3,.3))]:
   target=Vector((0,-.02,.32));cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'{name}_{view}_{i:02}.png');bpy.ops.render.render(write_still=True)
 report[name]=rows
(OUT/'probes.json').write_text(json.dumps(report,indent=2)+'\n');print('PROBES',report,flush=True)
