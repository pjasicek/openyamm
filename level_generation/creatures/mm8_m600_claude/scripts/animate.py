"""Native-timed slime motion, sampled at 120 Hz so each native hold is exactly 15 keys."""
from pathlib import Path
import bpy, json, math, sys
import numpy as np
from mathutils import Quaternion, Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['NightmareRig'];o=bpy.data.objects['Nightmare'];sc=bpy.context.scene;sc.render.fps=120
cfg=json.loads((P/'work/rig.json').read_text());chains=cfg['chains'];tau=2*math.pi
full='--full' in sys.argv

def rotation(name,x=0,y=0,z=0):
 pb=rig.pose.bones[name];q=pb.bone.matrix_local.to_quaternion()
 pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q.inverted()@Quaternion((0,0,1),z)@Quaternion((0,1,0),y)@Quaternion((1,0,0),x)@q

def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)

def pulse(t,a,b,c):
 return smooth((t-a)/(b-a))*(1-smooth((t-b)/(c-b)))

def pose(clip,t):
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 phase=tau*t/(3 if clip=='Standing' else 1)
 attack=pulse(t,.12,.5,.94) if clip=='Attack' else 0
 recoil=pulse(t,0,.16,.625) if clip=='Hit' else 0
 collapse=smooth((t-.13)/.57) if clip in ('Death','Dead') else 0
 if clip=='Dead':collapse=1
 wobble=.03 if clip=='Standing' else .07
 if clip in ('Hit','Death','Dead'):wobble=0
 if clip=='Fidget':phase=tau*t/.625;wobble=.04
 for i,(name,point) in enumerate(cfg['lumps']):
  pb=rig.pose.bones[name];wave=math.sin(phase-point[1]*5-i*.3)*(1-collapse)
  pb.scale=(1-.015*wave+.08*collapse,1+wobble*wave-.62*collapse-.045*attack,1+.02*wave+.20*collapse)
 for k,c in enumerate(chains):
  n=len(c['names'])-1;side=-1 if c['joints'][0][0]<0 else 1
  base=.025 if clip=='Standing' else .085
  if clip in ('Death','Dead'):base=0
  for i,name in enumerate(c['names']):
   f=i/max(n,1);wave=math.sin(phase-k*.65-f*.9)
   pitch=base*wave/max(n,1)+.22*attack/max(n,1)-.20*recoil/max(n,1)
   spread=base*.65*math.cos(phase-k*.6-f*.9)/max(n,1)
   # Death folds outward across the side of the mound, with a curled terminal pod.
   spread+=side*collapse*((.25 if i==0 else 1.35/max(n-1,1)) if k<2 else .45/max(n,1))
   pitch+=collapse*(.65/max(n,1) if k<2 else .3/max(n,1))
   if i==n:
    pitch+=.04*math.sin(phase-k*.6-.8)*(1-collapse)
    spread-=side*collapse*.2
    pitch-=collapse*(.4 if k<2 else .15)
   if clip=='Attack' and c['name'].startswith('Eye'):
    # Independent reversals travel up each stalk, fading smoothly at both clip boundaries.
    envelope=.20*math.sin(math.pi*t)**2
    dart=tau*(1.6+.11*k)*t-k*1.37-f*.55
    pitch+=envelope*(.18*math.sin(dart)+.065*math.sin(tau*3.3*t+k*.81))/max(n,1)
    spread+=envelope*(.22*math.sin(dart*1.17+1.4)+.055*math.sin(tau*3.0*t-k))/max(n,1)
    if i==n:
     pitch+=envelope*.075*math.sin(dart+1.1)
     spread+=envelope*.085*math.sin(dart*1.17-.7)
   rotation(name,pitch,spread,0)
   # Slime retracts through joint translations; rigid tips keep unit scale in portable glTF.
   pb=rig.pose.bones[name]
   if i>0 or c['parent'].startswith('Neck'):
    delta=pb.bone.head_local-pb.bone.parent.head_local
    pb.location=pb.bone.matrix_local.to_3x3().inverted()@(-.38*collapse*delta)
   else:
    pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,-.62*collapse*pb.bone.head_local.z))
  # The whole chain root sinks with its soft attachment, with no length changes.

 for name,_,_,_ in cfg['jaws']:
  opening=.18*attack+.16*recoil+.22*collapse
  if clip=='Fidget':opening+=.11*math.sin(math.pi*t/.625)**2
  rotation(name,opening)
 for name in ['JawFront','FrontTop',*[n for n,c in cfg['embedded_eyes']]]:
  pb=rig.pose.bones[name];pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,collapse*(-.62*pb.bone.head_local.z+(.027 if name=='JawFront' else 0))))
 rig.pose.bones['Body'].scale=(1,1,1)
 rig.pose.bones['Body'].location=rig.pose.bones['Body'].bone.matrix_local.to_3x3().inverted()@Vector((0,-.018*attack,0))

clips={'Standing':3.,'Walking':1.,'Attack':1.}
if full:clips.update(Hit=.625,Death=.75,Dead=1.,Fidget=.625)
rig.animation_data_create()
for name,duration in clips.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a
 for frame in range(round(duration*120)+1):
  pose(name,frame/120)
  for pb in rig.pose.bones:
   pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('scale',frame=frame)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=round(duration*120)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None;pose('Standing',0)
# Dense evaluated-surface screen; authored slime compression is measured separately from stalk strain.
rest=np.array([v.co[:] for v in o.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
report={}
for name,duration in clips.items():
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 rows=[]
 for t in np.linspace(0,duration,max(3,round(duration*48)+1)):
  sc.frame_set(int(t*120),subframe=float(t*120%1));bpy.context.view_layer.update()
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-9)
  rows.append({'time':round(float(t),5),'floor':float(co[:,2].min()),'height':float(co[:,2].max()),'stretch_p99':float(np.percentile(ratio,99)),'stretch_max':float(ratio.max()),'edge':int(ratio.argmax())})
 report[name]={'floor_min':min(r['floor'] for r in rows),'stretch_p99':max(r['stretch_p99'] for r in rows),'stretch_max':max(r['stretch_max'] for r in rows),'samples':rows}
 print(name,{k:v for k,v in report[name].items() if k!='samples'})
 assert all(np.isfinite(list(r.values())).all() for r in rows)
 assert report[name]['floor_min'] > -.002,(name,report[name]['floor_min'])
(P/'review/deformation.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/animated.blend' if full else 'work/pilot.blend')))
# Reuse existing turnaround helper, with selected pose timing.
sys.path.insert(0,str(P.parent/'mm6_ooz_claude/scripts'));import common
common.setup_render();common.workbench_clay(sc)
for name,t in [('Standing',0),('Walking',.25),('Attack',.5)]+([('Hit',.16),('Death',.5),('Dead',.5)] if full else []):
 rig.animation_data.action=bpy.data.actions[name];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(round(t*120))
 common.render_views(str(P/f'review/pose_{name}'),.5,1.45,views=('front','left','three_quarter'),resolution=(400,500))
