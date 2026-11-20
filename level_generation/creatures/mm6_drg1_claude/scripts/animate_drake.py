"""Native-informed procedural flying, breath release and death recoil. 24 fps, in-place.

The death burns in the air, as the native drake (recoil, thrash, failing wings); its burning is the engine burn
effect (actors.yml death_effect: burn);
no skeletal shrinking, flame cards or remains since v8."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/burn_v8_source.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=24
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
axes={n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
def ss(x):x=max(0,min(1,x));return x*x*(3-2*x)
def rot(n,axis,angle):
 pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axes[n]@Vector(axis),angle)
def lowest():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();low=min(v.co.z for v in em.vertices);ev.to_mesh_clear();return low
def hover(need,window=8):
 # Smallest smooth lift above every frame's need: a running maximum, then a moving average of the same width (each
 # averaged maximum covers the centre frame). Per-frame anchoring bounced the body on every wing downstroke.
 peak=[max(need[max(0,i-window):i+window+1]) for i in range(len(need))]
 return [sum(peak[max(0,i-window):i+window+1])/len(peak[max(0,i-window):i+window+1]) for i in range(len(peak))]
def pose(name,t,duration,lift=None):
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 phase=2*math.pi*t/duration;flap=phase;speed=1 if name!='Running' else 1.15
 pitch=0.;bank=.025*math.sin(phase);neck=0.;yaw=0.;jaw=-.18;shift=Vector((0,0,.008*math.sin(phase)))
 down=.03+.28*math.sin(flap);fold=.06*math.sin(flap-.6);wingAmp=1.;tailPhase=phase;tailAmp=1.
 if name in ('Walking','Running'):pitch=.12 if name=='Walking' else .21;down=.30+.32*math.sin(flap);neck=-pitch*.7
 if name=='Fidget':yaw=.20*math.sin(phase);bank=.06*math.sin(phase);neck=.04*math.sin(phase*2)
 if name in ('Attack','Cast'):
  prep=ss(t/.64)*(1-ss((t-.70)/.20));release=ss((t-.68)/.22)*(1-ss((t-1.02)/.42))
  pitch=-.16*prep+.15*release;neck=-.18*prep+.14*release;yaw=.11*prep-.05*release;bank=-.05*prep+.04*release
  jaw=-.18+.10*prep+.45*release;down=.22-.18*prep+.35*release;fold=.02+.10*release;shift=Vector((.015*prep,.045*prep-.06*release,.015*prep))
 if name=='Hit':
  h=ss(t/.12)*(1-ss((t-.12)/.60));pitch=-.17*h;neck=-.16*h;bank=.08*h;jaw=-.18+.22*h;down=.27-.22*h;shift.y=.04*h
 death=name in ('Death','Dead')
 if death:
  # Burns in the air, as the native drake: a roaring recoil, a frantic airborne thrash (fast irregular wing beats,
  # lashing tail, jerking bank and yaw, a slight lift), then the wings give out and the body sags under the fire.
  t=2.0 if name=='Dead' else t;tau=2*math.pi
  recoil=ss(t/.15)*(1-ss((t-.45)/.40));thrash=ss((t-.15)/.20)*(1-ss((t-1.25)/.50));fail=ss((t-1.1)/.7)
  beat=tau*3.2*t;flap=beat
  down=(1-fail)*(.10+.45*math.sin(beat)+.10*math.sin(1.7*beat+1))+.40*fail;fold=.30*fail+.08*thrash*math.sin(beat-.6)
  pitch=-.28*recoil+.06*thrash*math.sin(tau*1.9*t)+.20*fail;neck=-.30*recoil+.12*thrash*math.sin(tau*1.5*t+1)+.30*fail
  bank=.14*thrash*math.sin(tau*1.3*t+.5);yaw=.18*thrash*math.sin(tau*.9*t)
  jaw=-.18+.55*max(recoil,.6*thrash*(.5+.5*math.sin(tau*2.2*t)))
  wingAmp=1+2.5*thrash;tailPhase=tau*1.8*t;tailAmp=1+6*thrash
  shift.z=.05*thrash+.02*thrash*math.sin(beat)-.12*fail
 rot('Root',(1,0,0),pitch);rot('Root',(0,1,0),bank);rig.pose.bones['Root'].location=axes['Root']@shift
 for i in range(1,4):rot('Neck'+str(i),(1,0,0),neck/3);rot('Neck'+str(i),(0,0,1),yaw/3)
 rot('Head',(1,0,0),-.02*math.sin(phase)-neck*.2);rot('Jaw',(1,0,0),jaw)
 for i in range(1,10):
  amp=(.018+.003*i)*tailAmp;rot('Tail'+str(i),(0,0,1),amp*math.sin(tailPhase-i*.50));rot('Tail'+str(i),(1,0,0),.012*tailAmp*math.sin(tailPhase-i*.55))
 for side,sg in [('L',1),('R',-1)]:
  rot(side+'Wing0',(0,1,0),sg*down);rot(side+'Wing1',(0,1,0),sg*(.04+.08*wingAmp*math.sin(flap-.45)));rot(side+'Wing2',(0,1,0),sg*.05*wingAmp*math.sin(flap-.85));rot(side+'Wing1',(0,0,1),sg*fold)
  for limb in ['Fore','Hind']:
   rot(side+limb+'Upper',(1,0,0),-.06+.04*math.sin(phase-.8));rot(side+limb+'Lower',(1,0,0),.10+.05*math.sin(phase-1.2));rot(side+limb+'Foot',(1,0,0),-.06)
 # Locomotion retains the prior forward flight pose; upright posing is for hovering/actions.
 if name not in ('Walking','Running'):
  # Native drake hovers chest-up, with short tucked forelimbs and hanging hind legs.
  for i in range(4,10):
   rot(f'Tail{i}',(0,0,1),.12 if i<7 else .24)
   rot(f'Tail{i}',(1,0,0),.08 if i<7 else .20)
  upright=.98
  rot('Root',(1,0,0),-upright)
  for n,a in [('Neck1',.64),('Neck2',.24),('Neck3',.10)]:rot(n,(1,0,0),a)
  for side in ['L','R']:
   # Keep the wing plane aligned for lift as the trunk stands up.
   pb=rig.pose.bones[side+'Wing0'];pb.rotation_quaternion=Quaternion(axes[pb.name]@Vector((1,0,0)),upright)@pb.rotation_quaternion
   rot(side+'ForeUpper',(1,0,0),.80)
   rot(side+'ForeLower',(1,0,0),-.20)
   rot(side+'ForeFoot',(1,0,0),.30)
   rot(side+'HindUpper',(1,0,0),.82)
   rig.pose.bones[side+'HindUpper'].scale=(1.,1.45,1.)
   rig.pose.bones[side+'HindLower'].scale=(1.,1.25,1.)
 bpy.context.view_layer.update()
 # Preserve origin anchoring. Small tail lag may lift the actor by millimetres, never a fixed hover pedestal. A given
 # lift replaces the per-frame anchoring (the death's smooth hover, below).
 if lift is None:
  low=lowest()
  if low<0:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,-low));bpy.context.view_layer.update()
 elif lift>0:rig.pose.bones['Root'].location+=axes['Root']@Vector((0,0,lift));bpy.context.view_layer.update()
clips={'Standing':27,'Walking':24,'Running':20,'Fidget':48,'Attack':36,'Cast':36,'Hit':22,'Death':48,'Dead':24};report={}
deathLift=0.
for name,nframes in clips.items():
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 mins=[];lifts=None
 if name=='Death':
  need=[]
  for f in range(nframes+1):pose(name,f/24,nframes/24,lift=0.);need.append(max(0.,-lowest()))
  lifts=hover(need);deathLift=lifts[-1]
 if name=='Dead':lifts=[deathLift]*(nframes+1)
 for f in range(nframes+1):
  pose(name,f/24,nframes/24,lifts[f] if lifts else None)
  for pb in rig.pose.bones:
   pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();mins.append(min(v.co.z for v in em.vertices));ev.to_mesh_clear()
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'frames':nframes,'duration':nframes/24,'min_z':min(mins),'impact':.9375 if name in ['Attack','Cast'] else None}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0);sc.frame_start=0;sc.frame_end=48
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_repaired.blend'));(P/'work/clips.json').write_text(json.dumps(report,indent=2));print('CLIPS',json.dumps(report))
