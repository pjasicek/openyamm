"""Rigid stone motion: cap/jaw bite and discharge, grounded rocking and a rubble collapse."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Euler
P=Path(__file__).resolve().parents[1];FPS=96
full='--full' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
spec=json.loads((P/'work/rig_spec.json').read_text());groups=spec['groups']
co=np.array([tuple(v.co) for v in body.data.vertices]);coords={}
for name in groups:
 ids=[v.index for v in body.data.vertices if any(body.vertex_groups[w.group].name==name for w in v.groups)]
 coords[name]=co[ids];groups[name]['inverse_bind']=rig.data.bones[name].matrix_local.inverted()
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def curve(t,keys):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:return x+(y-x)*ease((t-a)/(b-a))
 return keys[-1][1]
def rotate(name,xyz):rig.pose.bones[name].rotation_euler=tuple(math.radians(x) for x in xyz)
def points(name):
 m=np.array(rig.pose.bones[name].matrix @ groups[name]['inverse_bind']);return coords[name]@m[:3,:3].T+m[:3,3]
def update():bpy.context.view_layer.update()
def pose(clip,t):
 for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.matrix_basis=Matrix.Identity(4)
 cap=5;pitch=0;roll=0;jaw=0
 if clip=='Standing':
  cap+=.8*math.sin(2*math.pi*t/3);roll=.35*math.sin(2*math.pi*t/3)
 elif clip=='Walking':
  roll=5.5*math.sin(2*math.pi*t);pitch=4+1.5*math.cos(4*math.pi*t);cap=4+1.5*math.cos(4*math.pi*t)
 elif clip=='Attack':
  cap=curve(t,[(0,5),(.25,-10),(.72,-28),(.88,-30),(1,1),(1.1,-5),(1.5,5)])
  pitch=curve(t,[(0,0),(.65,-6),(.87,-8),(1,11),(1.12,7),(1.5,0)])
  jaw=curve(t,[(0,0),(.7,5),(.88,5),(1,-1),(1.5,0)])
 elif clip=='Cast':
  cap=curve(t,[(0,5),(.35,-20),(.8,-34),(1,-30),(1.12,-9),(1.5,5)])
  pitch=curve(t,[(0,0),(.65,-4),(.92,-6),(1,5),(1.5,0)])
  roll=math.sin(17*t)*1.3*math.sin(math.pi*min(t,1)) if t<1 else 0
  jaw=curve(t,[(0,0),(.55,6),(1,6),(1.5,0)])
 elif clip=='Hit':
  cap=curve(t,[(0,5),(.13,-15),(.3,-6),(.625,5)])
  pitch=curve(t,[(0,0),(.10,-9),(.28,-3),(.625,0)])
  roll=curve(t,[(0,0),(.14,-4),(.625,0)])
 elif clip in ('Death','Dead'):
  t=1.25 if clip=='Dead' else t
  cap=curve(t,[(0,5),(.16,-23),(.5,-23),(1.25,0)])
  pitch=curve(t,[(0,0),(.16,-7),(.5,0),(1.25,0)])
 rotate('Core',(pitch,roll,0));rotate('Cap',(cap,0,0));rotate('Jaw',(jaw,0,0));update()
 if clip in ('Death','Dead') and t>.16:
  for i,(name,g) in enumerate(groups.items()):
   c=np.array(g['center']);rng=np.random.default_rng(588+i)
   angle=math.atan2(c[1],c[0]);radial=np.array([math.cos(angle),math.sin(angle)])
   tumble=Euler(tuple(rng.uniform(-1.6,1.6,3)),'XYZ').to_quaternion()
   landing=.7+float(rng.uniform(0,.35));u=ease((t-.16)/(landing-.16))
   start=rig.pose.bones[name].matrix.copy();start_q=start.to_quaternion();q=start_q.slerp(tumble,u)
   rot=np.array(q.to_matrix());local=coords[name]-c
   targetxy=c[:2]*(1.08 if g['owner']=='Base' else 1.35)+radial*(.1 if g['owner']=='Base' else .45)
   rest_rot=np.array(tumble.to_matrix());targetz=-float((local@rest_rot.T)[:,2].min())
   position=np.array(start.translation)*(1-u)+np.array([*targetxy,targetz])*u
   position[2]+=math.sin(math.pi*u)*(.18 if g['owner']=='Base' else .5)
   position[2]=max(position[2],-float((local@rot.T)[:,2].min()))
   rig.pose.bones[name].matrix=Matrix.Translation(position)@q.to_matrix().to_4x4()
  update()
 low=min(points(n)[:,2].min() for n in groups)
 rig.pose.bones['Root'].location.z=-float(low)
 update()
durations={'Standing':3,'Walking':1,'Attack':1.5}
if full:durations.update(Cast=1.5,Hit=.625,Death=1.25,Dead=1)
sc.render.fps=FPS;sc.render.fps_base=1;sc.frame_start=0
report={}
for clip,duration in durations.items():
 action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
 lows=[];highs=[];previous={}
 for frame in range(round(duration*FPS)+1):
  sc.frame_set(frame);pose(clip,frame/FPS)
  allco=np.concatenate([points(n) for n in groups]);lows.append(float(allco[:,2].min()));highs.append(float(allco[:,2].max()))
  for pb in rig.pose.bones:
   q=pb.matrix_basis.to_quaternion()
   if pb.name in previous and q.dot(previous[pb.name])<0:q.negate()
   previous[pb.name]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q
   pb.keyframe_insert('location',frame=frame,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
  assert abs(lows[-1])<1e-5
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 action.use_frame_range=True;action.frame_start=0;action.frame_end=round(duration*FPS)
 report[clip]={'duration':duration,'frames':round(duration*FPS)+1,'ground_min':min(lows),'height_range':[min(highs),max(highs)],'impact':1.0 if clip in ('Attack','Cast') else None}
rig.animation_data.action=None
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis=Matrix.Identity(4)
update();sc.frame_set(0)
tag='animated' if full else 'pilot'
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{tag}.blend'))
for o in bpy.data.objects:o.select_set(o.type in ('ARMATURE','MESH','EMPTY'))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/f'export/{tag}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_optimize_animation_size=False)
(P/f'work/{tag}_motion.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
