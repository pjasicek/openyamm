import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
def ss(t):t=max(0,min(1,t));return t*t*(3-2*t)
def rot(n,axis,a):rig.pose.bones[n].rotation_quaternion @= Quaternion(axes[n]@Vector(axis),a)
def pose(name,t,d):
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 phase=t/d*math.tau;flap=.35-.32*math.cos(phase);pitch=-.22;neck=.09;yaw=.015*math.sin(phase);bank=.018*math.sin(phase);jaw=0.;shift=Vector((0,0,.018*math.sin(phase)));fold=.05*math.sin(phase-.5);curl=0
 if name in ('Walking','Running'):pitch=.03 if name=='Walking' else .12;neck=-pitch*.6;flap=.40-.38*math.cos(phase)
 if name=='Fidget':yaw=.18*math.sin(phase);neck+=.07*math.sin(phase);bank=.05*math.sin(phase)
 if name in ('Attack','Cast'):
  prep=ss(t/.38)*(1-ss((t-.42)/.20));hit=ss((t-.40)/.20)*(1-ss((t-.76)/.365))
  pitch=-.22-.15*prep+.23*hit;neck=.09-.12*prep+.18*hit;yaw=.08*prep-.035*hit;bank=-.04*prep+.03*hit;jaw=-.08*prep+.40*hit;flap=.16+.53*hit;fold=.10*hit;shift+=Vector((.018*prep,.06*prep-.09*hit,.03*prep));curl=.06*prep
 if name=='Hit':
  h=ss(t/.14)*(1-ss((t-.14)/.80));pitch-=.16*h;neck-=.12*h;bank=.10*h;jaw=.25*h;flap=.20;shift.y=.08*h
 if name in ('Death','Dead'):
  t=1.5 if name=='Dead' else t;c=ss(t/.65);fall=ss((t-.75)/.75);pitch=-.22-.20*c+.45*fall;neck=.09-.15*c+.2*fall;yaw=.12*math.sin(t*5)*c;bank=.2*c;jaw=.35*c;flap=.35+.3*fall;fold=.20*c;curl=.30*c;shift.z=-.1*fall
 rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rig.pose.bones['Root'].location=axes['Root']@shift
 for i in range(1,4):rot('Neck'+str(i),(1,0,0),neck/3);rot('Neck'+str(i),(0,0,1),yaw/3)
 rot('Head',(1,0,0),-neck*.2);rot('Jaw',(1,0,0),jaw)
 for i in range(1,10):
  rot('Tail'+str(i),(0,0,1),(.012+.004*i)*math.sin(phase-i*.4)+curl*.4);rot('Tail'+str(i),(1,0,0),.014*math.sin(phase-i*.4)+curl*.5)
 for side,sg in [('L',1),('R',-1)]:
  rot(side+'Wing0',(0,1,0),sg*flap);rot(side+'Wing1',(0,1,0),sg*.09*math.sin(phase-.5));rot(side+'Wing2',(0,1,0),sg*.06*math.sin(phase-.8));rot(side+'Wing1',(0,0,1),sg*fold)
  for limb in ['Fore','Hind']:
   rot(side+limb+'Upper',(1,0,0),.035*math.sin(phase-.7));rot(side+limb+'Lower',(1,0,0),.05*math.sin(phase-1.1))
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();low=min(v.co.z for v in em.vertices);ev.to_mesh_clear()
 if low<0:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,-low))
 bpy.context.view_layer.update()
report={};clips={'Standing':27,'Walking':27,'Running':21,'Fidget':54,'Attack':27,'Cast':27,'Hit':27,'Death':36,'Dead':24}
for name,nf in clips.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=a;mins=[]
 for f in range(nf+1):
  pose('Death',1.5,1.5) if name=='Dead' else pose(name,f/24,nf/24)
  for pb in rig.pose.bones:
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();mins.append(min(v.co.z for v in em.vertices));ev.to_mesh_clear()
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 assert min(mins)>-.001
 report[name]={'duration':nf/24,'frames':nf,'min_z':min(mins),'impact':.65625 if name in ['Attack','Cast'] else None}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0);sc.frame_start=0;sc.frame_end=54
(P/'work/clips.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'));print('CLIPS',report)
