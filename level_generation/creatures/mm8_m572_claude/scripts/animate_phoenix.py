"""Native-timed Phoenix flight, talon strike, recoil and back-fall. 32 fps, fixed bone lengths."""
import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
P=Path(__file__).resolve().parents[1]
attack_only='--attack-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(P/('work/anim_uv.blend' if attack_only else 'work/rig_v1.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=32
for a in list(bpy.data.actions):
 if not attack_only or a.name in ('Attack','Cast'):bpy.data.actions.remove(a)
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
rest=np.array([v.co[:] for v in body.data.vertices]);wing=np.array([v.value for v in body.data.attributes['wing'].data],bool)
E=np.array([e.vertices[:] for e in body.data.edges]);EL=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
def ss(x):x=max(0,min(1,x));return x*x*(3-2*x)
def ramp(t,points):
 for (a,x),(b,y) in zip(points[:-1],points[1:]):
  if a<=t<=b:return x+(y-x)*ss((t-a)/(b-a))
 return points[0][1] if t<points[0][0] else points[-1][1]
def rot(n,axis,angle):
 pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axes[n]@Vector(axis),angle)
def surf():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def worldrot(pb,q):
 h=pb.head.copy();pb.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix;bpy.context.view_layer.update()
def pose(role,t,dur):
 if role=='Dead':t=1.125
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 cycle=dur if role in ('Standing','Walking','Running','Attack','Cast','Hit') else 1.
 p=t/cycle%1;phase=2*math.pi*p
 elev=math.radians(ramp(p,[(0,30),(.125,-5),(.25,-45),(.375,-35),(.5,-5),(.625,30),(.75,60),(.875,55),(1,30)]))
 gait=role in ('Walking','Running');pitch=(.11 if gait else 0)+.025*math.sin(phase-.4);bank=.015*math.sin(phase)
 # Flight altitude belongs to the engine, as in the accepted Bat.
 shift=Vector((0,0,.012*math.sin(phase-1.1)));jaw=.04;chamber=kick=hit=fall=0.
 if role in ('Attack','Cast'):
  chamber=ramp(t,[(0,0),(.3125,1),(.625,.85),(.875,0),(1.25,0)])
  kick=ramp(t,[(0,0),(.625,0),(.875,1),(.96875,.75),(1.09375,.25),(1.25,0)])
  pitch-=.70*chamber;pitch+=.36*kick;shift.y=.055*chamber-.095*kick;shift.z+=.065*chamber-.035*kick
  elev=math.radians(ramp(t,[(0,30),(.3125,75),(.625,55),(.875,-40),(1.09375,5),(1.25,30)]));jaw+=.50*max(chamber,kick)
 if role=='Hit':
  hit=ramp(t,[(0,0),(.105,1),(.24,.70),(.625,0)]);pitch-=.40*hit;bank+=.42*hit;shift.x+=.025*hit;shift.y+=.055*hit;shift.z-=.02*hit;jaw+=.40*hit
  elev+=.28*hit
 if role in ('Death','Dead'):
  fall=ss((t-.08)/.77);hit=ss(t/.12)*(1-ss((t-.20)/.45));pitch=-.40*hit-2.70*fall;bank=.13*fall
  shift=Vector((.015*fall,.06*fall,0.0));elev=(1-fall)*elev;jaw=.04+.45*hit+.12*fall
 rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rig.pose.bones['Root'].location=axes['Root']@shift
 rot('Neck',(1,0,0),-.30*pitch*(1-fall));rot('Head',(1,0,0),-.20*pitch*(1-fall));rot('Jaw',(1,0,0),jaw)
 if role=='Fidget':rot('Head',(0,0,1),.38*math.sin(math.pi*t/dur)**2*math.sin(2*math.pi*t/dur))
 rot('Tail',(1,0,0),-.08*math.sin(phase-.7)*(1-fall)+.22*chamber+.12*fall)
 rot('Tail',(0,0,1),.025*math.sin(phase-1)*(1-fall)+.08*fall)
 for sd,sg in [('L',1),('R',-1)]:
  rot(sd+'Wing0',(0,1,0),sg*(.38-elev)*(1-fall));rot(sd+'Wing0',(1,0,0),-pitch*.55*(1-fall))
  recover=max(0,math.sin(phase-math.pi))
  rot(sd+'Wing1',(0,1,0),sg*.14*math.sin(phase-.35)*(1-fall));rot(sd+'Wing1',(0,0,1),sg*.22*recover*(1-fall))
  rot(sd+'Wing2',(0,1,0),sg*.20*math.sin(phase-.75)*(1-fall));rot(sd+'Wing2',(0,0,1),-sg*.16*recover*(1-fall))
  pb=rig.pose.bones[sd+'Wing2'];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((0,1,0),sg*.28*recover*(1-fall))
  rot(sd+'Thigh',(1,0,0),(-.16-.035*math.sin(phase-.5)-.30*chamber-1.20*kick)*(1-fall)-.25*fall)
  rot(sd+'Tarsus',(1,0,0),(.15+.45*chamber+.08*kick)*(1-fall)+.38*fall)
  rot(sd+'Foot',(1,0,0),-.12+.20*chamber-.48*kick+.20*fall)
  for j in range(4):rot(sd+'Toe'+str(j),(1,0,0),(.08 if j<3 else -.05)*(1-kick)+.12*chamber+.12*fall)
 bpy.context.view_layer.update()
 if fall:
  # The torso lands first; each wing then relaxes onto the same ground plane.
  a=surf();low=float(a[~wing,2].min());rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,max((.003-low)*fall,.002-low)));bpy.context.view_layer.update()
  for sd,sg in [('L',1),('R',-1)]:
   pb=rig.pose.bones[sd+'Wing0'];mask=wing&(rest[:,0]*sg>.09);cloud=surf()[mask]
   normal=Vector(np.linalg.eigh(np.cov(cloud.T))[1][:,0]);target=Vector((0,0,1 if normal.z>0 else -1))
   q=Quaternion((1,0,0,0)).slerp(normal.rotation_difference(target),fall);worldrot(pb,q)
   a=surf();low=float(a[mask,2].min())
   if low<.002:
    base=pb.matrix.copy();v=rig.pose.bones[sd+'Wing2'].tail-pb.head;axis=Vector((v.y,-v.x,0)).normalized()
    def clear(angle):
     pb.matrix=base;worldrot(pb,Quaternion(axis,angle));return float(surf()[mask,2].min())
    lo,hi=0.,1.
    assert clear(hi)>.002,(role,t,sd,'wing floor')
    for _ in range(10):
     mid=(lo+hi)/2
     if clear(mid)<.002:lo=mid
     else:hi=mid
    clear(hi)
  low=float(surf()[:,2].min())
  if low<.002 or fall==1:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,.002-low));bpy.context.view_layer.update()
 if role in ('Death','Dead'):
  low=float(surf()[:,2].min())
  if low<.002:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,.002-low));bpy.context.view_layer.update()
 return {'chamber':chamber,'strike':kick,'fall':fall}
clips={'Standing':32,'Walking':32,'Running':24,'Fidget':64,'Attack':40,'Cast':40,'Hit':20,'Death':36,'Dead':32};report={}
if attack_only:
 clips={name:clips[name] for name in ('Attack','Cast')};report=json.loads((P/'work/clips.json').read_text())
for name,frames in clips.items():
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 bounds=[];stretch=[];first=None;trace=[];lastquat={}
 for f in range(frames+1):
  intent=pose(name,f/32,frames/32)
  for pb in rig.pose.bones:
   if pb.name in lastquat and pb.rotation_quaternion.dot(lastquat[pb.name])<0:pb.rotation_quaternion.negate()
   lastquat[pb.name]=pb.rotation_quaternion.copy()
   for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=f)
  a=surf();assert np.isfinite(a).all();bounds.append([a.min(0).tolist(),a.max(0).tolist()]);first=a.copy() if first is None else first
  ratio=np.linalg.norm(a[E[:,0]]-a[E[:,1]],axis=1)/np.maximum(EL,1e-8);stretch.append(np.percentile(ratio[EL>1e-5],[99,100]).tolist())
  trace.append({'t':f/32,'left_talon':list(rig.pose.bones['LToe1'].tail),'beak':list(rig.pose.bones['Head'].tail),**intent})
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 delta=float(np.linalg.norm(a-first,axis=1).max())
 if name in ('Standing','Walking','Running','Fidget','Dead'):assert delta<1e-5,(name,delta)
 report[name]={'frames':frames,'duration':frames/32,'impact':.875 if name in ('Attack','Cast') else None,'bounds':bounds,'stretch':np.max(stretch,axis=0).tolist(),'loop_delta':delta,'trace':trace}
 print(name,'floor',min(b[0][2] for b in bounds),'stretch',report[name]['stretch'],flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
(P/'work/clips.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/anim_uv.blend' if attack_only else 'work/anim_v1.blend')))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.render.resolution_x=1000;sc.render.resolution_y=850;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for clip,frame,view,target,scale,d in [
 ('Standing',24,'front_up',(0,0,.20),1.15,(0,-1,0)),('Standing',8,'front_down',(0,0,.20),1.15,(0,-1,0)),
 ('Walking',16,'side_mid',(0,0,.20),.85,(1,0,0)),('Attack',9,'chamber',(0,0,.20),1.35,(1,-1,.2)),
 ('Attack',28,'strike',(0,0,.20),1.35,(1,-1,.2)),('Attack',28,'beak',(0,-.19,.13),.18,(1,-1,.1)),
 ('Hit',4,'recoil',(0,0,.20),1.15,(1,-1,.2)),('Death',16,'fall',(0,0,.18),1.10,(1,-1,.4)),
 ('Dead',0,'corpse',(0,0,.10),1.15,(1,-1,.6)),('Dead',0,'corpse_top',(0,0,0),1.15,(0,0,1))]:
 if attack_only and clip not in ('Attack','Cast'):continue
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);target=Vector(target);cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 sc.render.filepath=str(P/'review'/f'anim_{view}.png');bpy.ops.render.render(write_still=True)
