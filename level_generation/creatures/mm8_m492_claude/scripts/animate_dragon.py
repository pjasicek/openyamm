"""Native-informed flight, breath, recoil and a grounded side-collapse. 24 fps, in place."""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fx.blend'))
rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
rest=np.array([v.co[:] for v in o.data.vertices]);wing=np.array([v.value for v in o.data.attributes['wing'].data],bool)
wing_normals={}
for side,sg in [('L',1),('R',-1)]:
 cloud=rest[wing&(rest[:,0]*sg>.20)]
 normal=np.linalg.eigh(np.cov(cloud.T))[1][:,0]
 if normal[1]>0:normal=-normal
 wing_normals[side]=Vector(normal)
core=(rest[:,1]>-.245)&(rest[:,1]<-.09)&(rest[:,2]>.13)&(rest[:,2]<.22)&(~wing)
def ss(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def rot(n,axis,a):
 pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axes[n]@Vector(axis),a)
def surface():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();a=np.empty(len(em.vertices)*3)
 em.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def pose(name,t,duration):
 if name=='Dead':t=1.375
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 period=duration if name in ('Standing','Walking','Running') else 1.375
 phase=2*math.pi*t/period;travel=.07 if name=='Walking' else .13 if name=='Running' else 0.
 pitch=-.14-.08*math.cos(phase)+travel;bank=.018*math.sin(phase);yaw=0.
 shift=Vector((0,0,.005*math.sin(phase-.5)))
 elevation=math.radians(35+30*math.cos(phase));jaw=.025;neck=-pitch*.8;headYaw=0.
 fall=0.;fold=0.;recoil=0.
 if name=='Fidget':
  headYaw=.25*math.sin(math.pi*t/duration)**2*math.sin(2*math.pi*t/duration)
  bank+=.035*math.sin(2*math.pi*t/duration)
 if name in ('Attack','Cast'):
  wind=ss(t/.75)*(1-ss((t-1.05)/.22));release=ss((t-1.05)/.20)*(1-ss((t-1.3)/.35))
  pitch-=.12*wind-.10*release;neck-=.15*wind-.16*release
  shift.y=.018*wind-.023*release;jaw=.025+.65*release
  elevation=math.radians(40+25*math.cos(phase));headYaw=.03*wind
 if name=='Hit':
  hit=ss(t/.12)*(1-ss((t-.15)/.8));pitch-=.16*hit;neck-=.18*hit;bank+=.08*hit
  shift.y=.025*hit;jaw+=.22*hit;elevation+=.12*hit
 death=name in ('Death','Dead')
 if death:
  recoil=ss(t/.25)*(1-ss((t-.45)/.40));fall=ss((t-.28)/.90);fold=ss((t-.25)/.65)
  pitch=(1-fall)*(-.14-.28*recoil)+.12*fall
  bank=math.pi*.5*fall;yaw=.12*fall;neck=-.45*recoil+.42*fall
  jaw=.025+.65*recoil+.16*fall;shift=Vector((.018*fall,.01*recoil,-.015*fall))
  elevation=(1-fold)*math.radians(40+25*math.cos(phase))
 rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rot('Root',(0,0,1),yaw)
 rig.pose.bones['Root'].location=axes['Root']@shift
 for i in range(1,4):
  rot(f'Neck{i}',(1,0,0),neck/3);rot(f'Neck{i}',(0,0,1),headYaw/3-(.3 if i==1 else 0)*fall)
 rot('Head',(1,0,0),-.012*math.sin(phase)*(1-fall)-.20*recoil);rot('Jaw',(1,0,0),jaw)
 for i in range(1,11):
  counter=-pitch*({1:.5,2:.3,3:.2}.get(i,0))*(1-fall)
  rot(f'Tail{i}',(0,0,1),(.012+.0015*i)*math.sin(phase-i*.45)*(1-fall)+.035*fall)
  rot(f'Tail{i}',(1,0,0),counter+.008*math.sin(phase-i*.35)*(1-fall)+.025*fall)
 for side,sg in [('L',1),('R',-1)]:
  rot(side+'Wing0',(1,0,0),-pitch*(1-fall))
  rot(side+'Wing0',(0,0,1),sg*(1.80 if side=='L' else 1.62)*fold)
  rot(side+'Wing0',(0,1,0),sg*(.570-elevation))
  rot(side+'Wing1',(0,1,0),sg*.06*math.sin(phase-.35)*(1-fold))
  rot(side+'Wing2',(0,1,0),sg*.10*math.sin(phase-.65)*(1-fold))
  rot(side+'Wing3',(0,1,0),sg*.06*math.sin(phase-.9)*(1-fold))
  rot(side+'Wing2',(0,0,1),sg*(.13*(1+math.sin(phase))*(1-fold)+.12*fold))
  # Feather the hand on the high stroke, matching the native edge-on recovery silhouettes.
  feather=(.20+.95*ss((math.cos(phase)+.2)/1.2))*(1-fold)
  pb=rig.pose.bones[side+'Wing2'];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((0,1,0),sg*feather)
  for limb in ['Fore','Hind']:
   upper=.09-pitch+.025*math.sin(phase-.7) if limb=='Hind' else -.15-.10*math.cos(phase)-pitch
   upper=upper*(1-fold)+(.6 if limb=='Hind' else -.55)*fold
   rot(side+limb+'Upper',(0,0,1),sg*(.50 if limb=='Hind' else -.80)*fold)
   rot(side+limb+'Upper',(1,0,0),upper)
   rot(side+limb+'Lower',(1,0,0),(.06+.035*math.sin(phase-1))*(1-fold)-.20*fold)
   rot(side+limb+'Foot',(1,0,0),-.04*(1-fall)+.15*fall)
 bpy.context.view_layer.update()
 if death:
  # Settle body and limbs first; wing-tip contact must not hold the corpse in the air.
  low=float(surface()[~wing,2].min());rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,(.002-low)*fall))
  bpy.context.view_layer.update()
  settle=ss((t-.35)/.65)
  for side,sg in [('L',1),('R',-1)]:
   pb=rig.pose.bones[side+'Wing0'];tip=rig.pose.bones[side+'Wing2']
   transform=tip.matrix@rig.data.bones[tip.name].matrix_local.inverted()
   normal=(transform.to_3x3()@wing_normals[side]).normalized()
   target=Vector((0,0,-1 if side=='L' else 1));q=normal.rotation_difference(target)
   q=Quaternion((1,0,0,0)).slerp(q,settle);h=pb.head.copy()
   pb.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix
   bpy.context.view_layer.update()
   # Lay membranes on the dorsal side, clear of the tucked claws and the tail.
   direction=rig.pose.bones[side+'Wing3'].tail-h
   target=Vector((.75,1,0)) if side=='L' else Vector((1,.6,0))
   angle=math.atan2(target.y,target.x)-math.atan2(direction.y,direction.x)
   angle=(angle+math.pi)%(2*math.pi)-math.pi
   pb.matrix=Matrix.Translation(h)@Quaternion(Vector((0,0,1)),angle*settle).to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix
   bpy.context.view_layer.update()
   # Tilt the settled membrane just enough to clear the floor, preserving fixed bone lengths.
   mask=wing&(rest[:,0]*sg>.065);base=pb.matrix.copy()
   direction=rig.pose.bones[side+'Wing3'].tail-h;axis=Vector((direction.y,-direction.x,0)).normalized()
   def wing_floor(angle):
    pb.matrix=Matrix.Translation(h)@Quaternion(axis,angle).to_matrix().to_4x4()@Matrix.Translation(-h)@base
    bpy.context.view_layer.update();return float(surface()[mask,2].min())
   if wing_floor(0)<.002:
    lo,hi=0.,.8
    assert wing_floor(hi)>.002,(name,t,side,'wing cannot clear floor')
    for _ in range(10):
     mid=(lo+hi)/2
     if wing_floor(mid)<.002:lo=mid
     else:hi=mid
    wing_floor(hi)
  pb=rig.pose.bones['Tail1'];h=pb.head.copy();v=rig.pose.bones['Tail10'].tail-h
  target=v.copy();target.z=.035-h.z;flat=Vector((v.x,v.y,0)).normalized()
  target.x=flat.x*math.sqrt(max(0,v.length_squared-target.z*target.z))
  target.y=flat.y*math.sqrt(max(0,v.length_squared-target.z*target.z))
  q=Quaternion((1,0,0,0)).slerp(v.rotation_difference(target),fall)
  pb.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix
  bpy.context.view_layer.update()
 # Flame cards follow the mouth position but remain upright, as the native rising fire.
 mouth=rig.pose.bones['Socket_Mouth'].matrix.translation.copy()
 for i in range(8):
  pb=rig.pose.bones[f'MouthFire{i}'];pb.location=axes[pb.name]@(mouth-rig.data.bones[pb.name].head_local)
  active=death and .25<=t<1.25 and int((t-.25)*12)%8==i
  size=(.75+.25*math.sin(t*31))*(1-ss((t-1.05)/.20)) if active else 1e-6
  pb.scale=(max(size,1e-6),)*3
 bpy.context.view_layer.update()
clips={'Standing':33,'Walking':33,'Running':26,'Fidget':66,'Attack':40,'Cast':40,'Hit':30,'Death':33,'Dead':24};report={}
for name,frames in clips.items():
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 bounds=[];coreLow=[]
 for f in range(frames+1):
  pose(name,f/24,frames/24)
  for pb in rig.pose.bones:
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  a=surface();assert np.isfinite(a).all();bounds.append([a.min(0).tolist(),a.max(0).tolist()]);coreLow.append(float(a[core,2].min()))
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'frames':frames,'duration':frames/24,'impact':1.25 if name in ('Attack','Cast') else None,'bounds':bounds,'core_floor':coreLow}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
(P/'work/clips.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for clip,frame,view,target,scale,d in [
 ('Standing',0,'front_up',(0,-.09,.26),1.15,(0,-1,.05)),
 ('Standing',16,'front_down',(0,-.09,.26),1.15,(0,-1,.05)),
 ('Walking',0,'side_up',(0,-.04,.24),1.1,(1,0,.03)),
 ('Attack',30,'jaw_side',(0,-.36,.27),.29,(1,0,0)),
 ('Death',12,'death_recoil',(0,-.09,.24),1.15,(1,-1,.5)),
 ('Death',24,'death_fall',(0,-.09,.24),1.15,(1,-1,.5)),
 ('Death',33,'death_end',(0,-.04,.15),1.05,(1,-1,.5)),
 ('Death',33,'death_front',(0,-.04,.15),1.05,(0,-1,.15)),
 ('Dead',0,'corpse_top',(0,.03,0),1.05,(0,0,1))]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame)
 target=Vector(target);cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 sc.render.filepath=str(P/'review'/f'anim_{view}.png');bpy.ops.render.render(write_still=True)
print('FLOORS',{k:min(b[0][2] for b in v['bounds']) for k,v in report.items()})
