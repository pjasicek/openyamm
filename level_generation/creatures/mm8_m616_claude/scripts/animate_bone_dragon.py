"""One native wingbeat, mouth release, recoil and an articulated backward collapse."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bat_claude/scripts'))
from posing import rotate_world,reset
full='--full' in sys.argv;uv='--uv' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/('uv_master.blend' if uv else 'rig_v1.blend')))
rig=bpy.data.objects['BoneDragon_Rig'];mesh=bpy.data.objects['BoneDragon'];sc=bpy.context.scene;sc.render.fps=24
rest=np.array([v.co[:] for v in mesh.data.vertices]);labels=np.array([d.value for d in mesh.data.attributes['anatomy_part'].data]);wing=np.isin(labels,[1,2]);core=labels==0
axes={b.name:b.matrix_local.to_3x3().inverted() for b in rig.data.bones}
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
def ss(x):x=np.clip(x,0,1);return float(x*x*(3-2*x))
def local(n,axis,degrees):
 pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axes[n]@Vector(axis),math.radians(degrees))
def surface():
 bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return c

def pose(name,t):
 reset(rig)
 if name=='Dead':t=.75
 phase=math.tau*t;fall=0.;fold=0.;jaw=-14.;pitch=0.;neck=0.;recoil=0.
 flap=12+60*math.cos(phase);bodybob=.004*math.sin(phase)
 if name in ('Attack','Cast'):
  wind=ss(t/.70)*(1-ss((t-1.0)/.3));blast=ss((t-.78)/.22)*(1-ss((t-1.05)/.26))
  neck=-14*wind+22*blast;pitch=-8*wind+5*blast;jaw=-14+39*blast
 if name=='Hit':
  recoil=ss(t/.12)*(1-ss((t-.18)/.57));pitch=-17*recoil;neck=-12*recoil;jaw=-14+28*recoil
 death=name in ('Death','Dead')
 if death:
  fall=ss((t-.16)/.59);fold=ss((t-.08)/.32);recoil=ss(t/.12)*(1-ss((t-.22)/.3))
  pitch=-170*fall-18*recoil;neck=50*fall-12*recoil;jaw=-14+30*recoil+14*fall
  flap=flap*(1-fold);bodybob=0.
 local('Root',(1,0,0),pitch);local('Root',(0,1,0),45*fall)
 rig.pose.bones['Root'].location=axes['Root']@Vector((0,0,bodybob))
 for i in range(1,4):local(f'Neck{i}',(1,0,0),neck/3)
 local('Head',(1,0,0),3*math.sin(phase-.3)*(1-fall));local('Jaw',(1,0,0),jaw);local('Head',(0,1,0),85*fall)
 for i in range(1,11):
  local(f'Tail{i}',(0,0,1),1.2*math.sin(phase-i*.5)*(1-fall)+1.4*fall)
  local(f'Tail{i}',(1,0,0),.5*math.sin(phase-i*.4)*(1-fall))
 for side,sg in [('L',1),('R',-1)]:
  # Rotate the frontal generation rest plane into the native swept, horizontal wing plane.
  local(side+'WingUpper',(0,1,0),-sg*flap)
  local(side+'WingUpper',(1,0,0),-68)
  local(side+'WingFore',(0,1,0),-sg*7*math.sin(phase-.45)*(1-fold))
  local(side+'WingHand',(1,0,0),12*math.sin(phase-.65)*(1-fold))
  for j in range(1,5):local(f'{side}WingFinger{j}',(1,0,0),(j-2)*1.2*math.sin(phase-.8)*(1-fold))
  local(side+'WingUpper',(0,0,1),sg*72*fold)
  local(side+'ForeUpper',(1,0,0),5*math.sin(phase-.5)*(1-fall)-22*fall)
  local(side+'ForeLower',(1,0,0),4*math.sin(phase-.8)*(1-fall)+16*fall)
  local(side+'HindUpper',(1,0,0),4*math.sin(phase-.8)*(1-fall)-25*fall)
  local(side+'HindLower',(1,0,0),3*math.sin(phase-1)*(1-fall)+12*fall)
 if death:
  a=surface();rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,(.014-a[core,2].min())*fall))
  bpy.context.view_layer.update()
  settle=ss((t-.36)/.39)
  # Hinge the neck clear of the floor while the rib cage remains grounded.
  neckbone=rig.pose.bones['Neck1'];neckbase=neckbone.matrix.copy();neckhead=neckbone.head.copy();headmask=np.isin(labels,[3,9])
  def neck_floor(deg):
   neckbone.matrix=Matrix.Translation(neckhead)@Matrix.Rotation(math.radians(deg),4,'X')@Matrix.Translation(-neckhead)@neckbase
   return float(surface()[headmask,2].min())
  if neck_floor(0)<.004 and settle>0:
   candidates=[(neck_floor(deg),deg) for deg in range(0,86,5)]
   valid=[(floor,deg) for floor,deg in candidates if floor>=-.008]
   chosen=min(valid,key=lambda pair:pair[1])[1] if valid else max(candidates)[1]
   neck_floor(chosen*settle)
  # Each caudal segment settles horizontally; an elevated tail must not prop up the ribs.
  for i in range(1,11):
   pb=rig.pose.bones[f'Tail{i}'];v=pb.tail-pb.head;target=Vector((v.x,v.y,0));q=Quaternion().slerp(v.rotation_difference(target),settle)
   h=pb.head.copy();pb.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix;bpy.context.view_layer.update()
  for side,label,sg in [('L',1,1),('R',2,-1)]:
   pb=rig.pose.bones[side+'WingUpper'];a=surface()[labels==label]
   n=Vector(np.linalg.eigh(np.cov(a.T))[1][:,0]);n=n if n.z>=0 else -n
   q=Quaternion().slerp(n.rotation_difference(Vector((0,0,1))),settle);h=pb.head.copy()
   pb.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@pb.matrix;bpy.context.view_layer.update()
   hand=rig.pose.bones[side+'WingHand'].head-h;target=Vector((sg*.9,.35,0))
   delta=(math.atan2(target.y,target.x)-math.atan2(hand.y,hand.x)+math.pi)%math.tau-math.pi
   rotate_world(rig,pb.name,'Z',math.degrees(delta)*settle)
  # Small remaining limb/tip clearance correction, measured on the actual evaluated mesh.
  a=surface();low=float(a[:,2].min());rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,max(0,.003-low)))
 bpy.context.view_layer.update()
clips={'Fly':24,'Attack':32}
if full:clips.update(Cast=32,Hit=18,Death=18,Dead=24)
report={}
for name,frames in clips.items():
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 bounds=[]
 for f in range(frames+1):
  pose(name,f/24)
  for pb in rig.pose.bones:
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  a=surface();assert np.isfinite(a).all();bounds.append([a.min(0).tolist(),a.max(0).tolist()])
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'frames':frames,'duration':frames/24,'loop':name in ('Fly','Dead'),'impact':1. if name in ('Attack','Cast') else None,'bounds':bounds}
rig.animation_data.action=bpy.data.actions['Fly'];sc.frame_set(0)
(P/'work/clip_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/('uv_master.blend' if uv else 'anim_v1.blend')))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=sc.camera;cam.data.type='ORTHO'
shots=[('Fly',0,'up',(0,-1,.05)),('Fly',6,'mid',(1,-1.5,.3)),('Fly',12,'down',(0,-1,.05)),('Fly',0,'side',(1,0,.05)),('Attack',24,'attack',(1,-1.5,.4))]
if full:shots += [('Death',9,'fall',(1,-1,.5)),('Dead',0,'corpse',(1,-1,.8)),('Dead',0,'corpse_side',(1,0,.1))]
for clip,fr,tag,d in shots:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(fr);a=surface();target=Vector((a.min(0)+a.max(0))/2);cam.data.ortho_scale=max(np.ptp(a,axis=0))*1.3
 cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'pilot_{tag}.png');bpy.ops.render.render(write_still=True)
print('CLIPS',{n:v['duration'] for n,v in report.items()});print('CORPSE_CORE_MIN',float(surface()[core,2].min()))
if full:assert float(surface()[core,2].min())<.04,'corpse torso is floating'
