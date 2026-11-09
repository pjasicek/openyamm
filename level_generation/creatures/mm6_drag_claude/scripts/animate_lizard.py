import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'));import posing as poseutil
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()};restfeet={s:rig.data.bones[s+'Foot'].head_local.copy() for s in ['L','R']};footq={s:rig.data.bones[s+'Foot'].matrix_local.to_quaternion() for s in ['L','R']}
def ss(t):t=max(0,min(1,t));return t*t*(3-2*t)
def rot(n,axis,a):rig.pose.bones[n].rotation_quaternion @= Quaternion(axes[n]@Vector(axis),a)
def coords():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def pose(name,t,d):
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 phase=t/d*math.tau;pitch=.04;neck=-.03;yaw=.012*math.sin(phase);bank=.009*math.sin(phase);jaw=-.08;shift=Vector((0,0,.0015*math.sin(phase)));arm=0;tailcancel=0;dead=name in ('Death','Dead');run=name=='Running';gait=name in ('Walking','Running')
 if gait:
  pitch=.62 if not run else .79;neck=-.24;bank=.045*math.sin(phase);shift=Vector((.007*math.sin(phase),-.012,-.018+.004*math.cos(2*phase)));tailcancel=-pitch*.78;arm=.07*math.sin(phase);yaw=.025*math.sin(phase)
 if name=='Fidget':yaw=.20*math.sin(phase);neck+=.07*math.sin(phase);arm=.09*math.sin(phase-.4)
 if name in ('Attack','Cast'):
  prep=ss(t/.36)*(1-ss((t-.52)/.20));hit=ss((t-.53)/.22)*(1-ss((t-.79)/.335))
  pitch=.04-.12*prep+.26*hit;neck=-.03-.12*prep+.20*hit;yaw=.12*prep-.06*hit;bank=-.035*prep+.02*hit;jaw=-.08+.03*prep+.30*hit;arm=-.12*prep-.30*hit;shift=Vector((.008*prep,.022*prep-.026*hit,-.007*prep-.009*hit));tailcancel=-.08*hit
  if name=='Cast':jaw+=.08*hit;yaw*=-.75;arm*=.7
 if name=='Hit':
  h=ss(t/.12)*(1-ss((t-.12)/.63));pitch-=.20*h;neck+=.18*h;bank=.13*h;yaw=-.10*h;jaw=.1*h;shift.y=.025*h;arm=-.3*h
 if dead:
  t=d if name=='Dead' else t;u=t/d;flinch=ss(u/.20)*(1-ss((u-.20)/.25));fall=ss((u-.20)/.65);settle=ss((u-.80)/.20)
  pitch=-.18*flinch+.15*fall;bank=1.50*fall;yaw=.13*fall;neck=.30*fall-.12*flinch;jaw=.10*(1-settle)-.10*settle;arm=-.55*flinch+.25*fall;shift=Vector((.05*fall,0,-.18*fall));tailcancel=-.12*fall
 rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rig.pose.bones['Root'].location=axes['Root']@shift
 rot('Spine1',(0,0,1),yaw*.3)
 for i in range(1,4):rot('Neck'+str(i),(1,0,0),neck/3);rot('Neck'+str(i),(0,0,1),yaw/3)
 rot('Head',(1,0,0),-neck*.25);rot('Jaw',(1,0,0),jaw)
 for i in range(1,9):
  sway=(.012+.004*i)*math.sin(phase-i*.4) if not dead else .035*ss(t/d/.7)
  rot('Tail'+str(i),(0,0,1),sway);rot('Tail'+str(i),(1,0,0),tailcancel if i==1 else .006*math.sin(phase-i*.5)*(not dead))
 for side,sg in [('L',1),('R',-1)]:
  rot(side+'UpperArm',(1,0,0),arm*(sg if gait else 1));rot(side+'ForeArm',(1,0,0),.03*math.sin(phase-.6)*(not dead));rot(side+'Hand',(1,0,0),-.03*math.sin(phase)*(not dead))
  if dead:rot(side+'Thigh',(1,0,0),(.35 if sg>0 else -.25)*ss(t/d/.7));rot(side+'Shin',(1,0,0),-.2*ss(t/d/.7))
 bpy.context.view_layer.update()
 if not dead:
  for side,sg in [('L',1),('R',-1)]:
   ankle=restfeet[side].copy();toe=0
   if gait:
    u=(t/d+(0 if sg>0 else .5))%1;duty=.61 if not run else .52;stride=.23 if not run else .31;lift=.043 if not run else .065
    if u<duty:ankle.y+=stride*(u/duty-.5)
    else:
     v=(u-duty)/(1-duty);ankle.y+=stride*(.5-ss(v));ankle.z+=lift*math.sin(math.pi*v);toe=-.17*math.sin(math.pi*v)
   hip=rig.pose.bones[side+'Thigh'].head.copy();pole=hip+Vector((sg*.025,-.4,0));poseutil.two_bone_ik(rig,side+'Thigh',side+'Shin',ankle,pole)
   foot=rig.pose.bones[side+'Foot'];q=Quaternion((1,0,0),toe)@footq[side];foot.matrix=Matrix.LocRotScale(foot.head.copy(),q,Vector((1,1,1)));bpy.context.view_layer.update()
 low=coords()[:,2].min()
 if low<0:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,-low))
 bpy.context.view_layer.update()
clips={'Standing':48,'Walking':18,'Running':14,'Fidget':48,'Attack':27,'Cast':27,'Hit':18,'Death':24,'Dead':24};report={}
for name,nf in clips.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=a;mins=[];heights=[]
 for f in range(nf+1):
  pose('Death',1.,1.) if name=='Dead' else pose(name,f/24,nf/24)
  for pb in rig.pose.bones:
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  co=coords();mins.append(float(co[:,2].min()));heights.append(float(co[:,2].max()))
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 assert min(mins)>-.001,(name,min(mins));report[name]={'duration':nf/24,'frames':nf,'min_z':min(mins),'height':[min(heights),max(heights)],'impact':.75 if name in ('Attack','Cast') else None}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0);sc.frame_start=0;sc.frame_end=48
(P/'work/clips.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.63,.67,.65);sc.display.shading.show_cavity=True;sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.30;target=Vector((0,-.1,.43));cam.location=target+Vector((3,-5,1.7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for clip,frames in [('Standing',[0]),('Walking',[0,4,9,13]),('Running',[0,4,8]),('Attack',[0,9,15,18,23]),('Cast',[9,18]),('Hit',[3]),('Death',[0,6,12,18,24])]:
 rig.animation_data.action=bpy.data.actions[clip]
 for f in frames:sc.frame_set(f);sc.render.filepath=str(P/'review'/f'motion_{clip}_{f:02}.png');bpy.ops.render.render(write_still=True)
print('CLIPS',json.dumps(report))
