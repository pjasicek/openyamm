"""Author body-led swimming and biting with a rigid carapace and independent paddle chains."""
from pathlib import Path
import bpy,sys,math,json
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
from posing import reset,rotate_world
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Turtle_Rig'];mesh=bpy.data.objects['Turtle'];sc=bpy.context.scene;sc.render.fps=48
rest=rig.data.bones['Root'].matrix_local.to_3x3();durations={'SwimIdle':1.,'Swim':1.,'Bite':1.10,'Hit':.75,'Fidget':.5,'Death':.875,'Dead':1.}
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
def curve(t,keys):
 # Cubic Hermite central tangents carry motion through intermediate source anchors.
 if t<=keys[0][0]:return keys[0][1]
 if t>=keys[-1][0]:return keys[-1][1]
 for i,((a,va),(b,vb)) in enumerate(zip(keys,keys[1:])):
  if t<=b:
   u=(t-a)/(b-a);p=keys[max(0,i-1)];q=keys[min(len(keys)-1,i+2)]
   ma=(vb-p[1])/(b-p[0]);mb=(q[1]-va)/(q[0]-a)
   return (2*u**3-3*u*u+1)*va+(u**3-2*u*u+u)*(b-a)*ma+(-2*u**3+3*u*u)*vb+(u**3-u*u)*(b-a)*mb

def pose(role,t):
 if role=='Dead':role,t='Death',durations['Death']
 reset(rig);phase=2*math.pi*t;moving=role=='Swim';amp=1 if moving else .5
 rig.pose.bones['Root'].location=rest.transposed()@Vector((0,0,.20+.012*amp*(1-math.cos(phase))))
 rotate_world(rig,'Shell','X',2*amp*math.sin(phase));rotate_world(rig,'Shell','Y',.7*amp*math.sin(phase))
 for side,sg in [('L',1),('R',-1)]:
  rotate_world(rig,'Front_'+side,'Y',sg*amp*24*math.sin(phase))
  rotate_world(rig,'Front_'+side,'Z',sg*amp*16*math.sin(phase-.6))
  rotate_world(rig,'Front_'+side,'X',amp*15*math.sin(phase+1.0))
  rotate_world(rig,'FrontTip_'+side,'Y',sg*amp*9*math.sin(phase-.5))
  rotate_world(rig,'Rear_'+side,'Y',sg*amp*11*math.sin(phase-.9))
  rotate_world(rig,'Rear_'+side,'Z',sg*amp*7*math.sin(phase-1.1))
  rotate_world(rig,'RearTip_'+side,'Y',sg*amp*5*math.sin(phase-1.3))
 for i in range(1,4):
  rotate_world(rig,f'Neck{i}','X',-.45*amp*math.sin(phase-i*.25))
  rotate_world(rig,f'Tail{i}','Z',amp*3*math.sin(phase-i*.5))
 rotate_world(rig,'Head','X',-.6*amp*math.sin(phase-.8))
 if role=='Bite':
  wind=smooth(t/.55)*(1-smooth((t-.57)/.17));strike=smooth((t-.57)/.18)*(1-smooth((t-.82)/.28))
  rotate_world(rig,'Shell','X',-13*wind+9*strike)
  for i,v in enumerate([-13,-9,8],1):rotate_world(rig,f'Neck{i}','X',v*wind+[8,6,-11][i-1]*strike)
  rotate_world(rig,'Head','X',9*wind-6*strike)
  jaw=curve(t,[(0,0),(.40,26),(.57,38),(.66,28),(.75,0),(.82,0),(1.10,0)])
  rotate_world(rig,'Jaw','X',max(0,jaw))
  rig.pose.bones['Root'].location+=rest.transposed()@Vector((0,.035*wind-.085*strike,.025*wind))
  for side,sg in [('L',1),('R',-1)]:
   rotate_world(rig,'Front_'+side,'Z',sg*(-15*wind+25*strike));rotate_world(rig,'Front_'+side,'Y',sg*(8*wind+8*strike))
   rotate_world(rig,'Rear_'+side,'Y',-sg*7*strike)
  for i in range(1,4):rotate_world(rig,f'Tail{i}','X',-3*strike)
 elif role=='Hit':
  a=smooth(t/.24)*(1-smooth((t-.24)/.51));rotate_world(rig,'Shell','X',-27*a)
  for i in range(1,4):rotate_world(rig,f'Neck{i}','X',-5*a)
  rotate_world(rig,'Head','X',8*a);rotate_world(rig,'Jaw','X',12*a)
  for side,sg in [('L',1),('R',-1)]:rotate_world(rig,'Front_'+side,'Y',-sg*22*a)
 elif role=='Fidget':
  a=math.sin(math.pi*t/.5)**2
  for i in range(1,4):rotate_world(rig,f'Neck{i}','Z',5*a)
  rotate_world(rig,'Head','Z',8*a);rotate_world(rig,'Head','X',-4*a)
 elif role=='Death':
  recoil=smooth(t/.20)*(1-smooth((t-.20)/.30));fall=smooth((t-.20)/.60)
  rotate_world(rig,'Shell','X',-37*recoil)
  for i in range(1,4):rotate_world(rig,f'Neck{i}','X',-8*recoil+5*fall);rotate_world(rig,f'Tail{i}','Z',-4*fall)
  rotate_world(rig,'Head','Z',22*fall);rotate_world(rig,'Jaw','X',18*fall)
  for side,sg in [('L',1),('R',-1)]:
   rotate_world(rig,'Front_'+side,'Y',sg*(-20*recoil-20*fall));rotate_world(rig,'FrontTip_'+side,'Y',-sg*8*fall)
   rotate_world(rig,'Rear_'+side,'Y',-sg*15*fall)
   rotate_world(rig,'Front_'+side,'Z',sg*55*fall)
  rotate_world(rig,'Root','Y',-28*fall,pivot=(0,.065,.35));rotate_world(rig,'Root','X',3*fall,pivot=(0,.065,.35))
  bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());low=min(v.co.z for v in ev.data.vertices)
  rig.pose.bones['Root'].location+=rest.transposed()@Vector((0,0,max(0,.005-low)*(1-fall)+(.005-low)*fall))
 bpy.context.view_layer.update()

rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
metrics={};ends={};shell=np.load(P/'work/shell_vertices.npy');base=np.array([v.co[:] for v in mesh.data.vertices])
for role,duration in durations.items():
 rig.animation_data_create();action=bpy.data.actions.new(role);rig.animation_data.action=action;times=sorted(set([f/48 for f in range(int(duration*48)+1)]+[duration]))
 minimum=1e9;shell_error=0
 for t in times:
  sc.frame_set(int(t*48),subframe=t*48-int(t*48));pose(role,t)
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=t*48,group=b.name);b.keyframe_insert('rotation_quaternion',frame=t*48,group=b.name)
  ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());co=np.array([v.co[:] for v in ev.data.vertices]);minimum=min(minimum,float(co[:,2].min()))
  matrix=rig.pose.bones['Shell'].matrix@rig.data.bones['Shell'].matrix_local.inverted()
  expected=np.array([tuple(matrix@Vector(v)) for v in base[shell]]);shell_error=max(shell_error,float(np.max(np.linalg.norm(co[shell]-expected,axis=1))))
  if t in (0,duration):ends[(role,t)]=co
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 action.use_fake_user=True;metrics[role]={'duration':duration,'samples':len(times),'minimum_z':minimum,'shell_rigidity_error':shell_error}
 assert minimum>-.0001,(role,minimum)
 assert shell_error<1e-5,(role,shell_error)
 if role in ['SwimIdle','Swim','Dead']:
  error=float(np.max(np.linalg.norm(ends[(role,0)]-ends[(role,duration)],axis=1)));metrics[role]['loop_error']=error;assert error<1e-5,(role,error)
assert np.max(np.abs(ends[('Death',.875)]-ends[('Dead',0)]))<1e-6
(P/'work/clip_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['Swim'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0);sc.frame_start=0;sc.frame_end=48
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
print('CLIPS',json.dumps(metrics),flush=True)
