"""Native flight, sword cut, recoil and backward collapse at 48 fps; no change to gameplay clocks."""
from pathlib import Path
import bpy,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from wasp_pose import base_pose,arms,rotate_world,reset,orient_hand
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv_sword_v2.blend'))
rig=bpy.data.objects['Wasp_Rig'];mesh=bpy.data.objects['Wasp'];sc=bpy.context.scene;sc.render.fps=48
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
durations={'Fly':.625,'FlyFast':.625,'Attack':1.25,'Hit':.625,'Fidget':.875,'Death':.875,'Dead':1.0}

def smooth(t):
 t=float(np.clip(t,0,1));return t*t*(3-2*t)
def pulse(t,a,b,c):return smooth((t-a)/(b-a))*(1-smooth((t-b)/(c-b)))
def keyed(t,keys):
 for (a,va),(b,vb) in zip(keys,keys[1:]):
  if t<=b:return np.array(va)*(1-smooth((t-a)/(b-a)))+np.array(vb)*smooth((t-a)/(b-a))
 return np.array(keys[-1][1])
def pose(role,t):
 if role=='Dead':role,t='Death',.875
 base_pose(rig,t,role=='FlyFast')
 if role=='Attack':
  # Coil on the sword side; the thorax drives the cut and the abdomen follows later.
  yaw=float(keyed(t,[(0,0),(.48,30),(.65,32),(.875,-25),(1.01,-34),(1.25,0)]))
  pitch=float(keyed(t,[(0,0),(.48,-10),(.65,-10),(.875,20),(1.01,17),(1.25,0)]))
  bank=float(keyed(t,[(0,0),(.48,-9),(.65,-9),(.875,12),(1.01,14),(1.25,0)]))
  rotate_world(rig,'Thorax','Z',yaw);rotate_world(rig,'Thorax','X',pitch);rotate_world(rig,'Thorax','Y',bank)
  rotate_world(rig,'Head','Z',-.35*yaw);rotate_world(rig,'Head','X',-.3*pitch)
  tail_yaw=float(keyed(max(0,t-.09),[(0,0),(.48,15),(.65,16),(.875,-18),(1.01,-24),(1.16,0)]))
  for i in range(1,5):
   rotate_world(rig,'Abdomen'+str(i),'Z',(tail_yaw-yaw)/4)
   rotate_world(rig,'Abdomen'+str(i),'X',-pitch*.14)
  target=keyed(t,[(0,(.15,-.205,.57)),(.48,(.19,-.12,.74)),(.65,(.19,-.12,.74)),(.875,(-.09,-.28,.53)),(1.01,(-.14,-.22,.44)),(1.25,(.15,-.205,.57))])
  blade=keyed(t,[(0,(.10,-.36,.93)),(.48,(.50,-.10,.86)),(.65,(.50,-.10,.86)),(.875,(-.62,-.75,-.23)),(1.01,(-.62,-.25,-.74)),(1.25,(.10,-.36,.93))])
  guard=keyed(t,[(0,(-.12,-.205,.61)),(.65,(-.14,-.17,.65)),(.875,(-.18,-.065,.64)),(1.01,(-.17,-.08,.62)),(1.25,(-.12,-.205,.61))])
  arms(rig,target,guard,blade)
  # Present the cutting edge to the sweep instead of striking with the flat.
  axis=(rig.pose.bones['Sword'].tail-rig.pose.bones['Sword'].head).normalized()
  rotate_world(rig,'Hand_L',axis,90*smooth(t/.4)*(1-smooth((t-1.04)/.21)))
  shift=keyed(t,[(0,(0,0,0)),(.48,(.015,.035,.012)),(.65,(.015,.035,.012)),(.875,(-.025,-.065,0)),(1.01,(-.035,-.08,0)),(1.25,(0,0,0))])
  rig.pose.bones['Root'].location+=rest['Root'].to_3x3().transposed()@Vector(shift)
 elif role=='Hit':
  a=pulse(t,0,.1875,.625);rotate_world(rig,'Thorax','X',-19*a);rotate_world(rig,'Thorax','Z',8*a);rotate_world(rig,'Head','X',-7*a)
  for i in range(1,5):rotate_world(rig,'Abdomen'+str(i),'X',-9*a)
  arms(rig,(.15,-.19,.57-.07*a),(-.12,-.19,.61+.075*a),(.1,-.36,.93-.8*a))
 elif role=='Fidget':
  a=math.sin(math.pi*t/.875)**2;rotate_world(rig,'Thorax','X',4*a);rotate_world(rig,'Head','Z',17*a);rotate_world(rig,'Head','X',-5*a)
  arms(rig,(.15,-.205,.57+.02*a),(-.12,-.205,.61),(.1+.15*a,-.36,.93))
 elif role=='Death':
  fall=smooth((t-.16)/.66);recoil=pulse(t,0,.16,.36)
  rotate_world(rig,'Thorax','X',-15*recoil)
  for i in range(1,5):rotate_world(rig,'Abdomen'+str(i),'X',-9*fall-5*recoil)
  arms(rig,(.15+.08*fall,-.205+.17*fall,.57),(-.12-.11*fall,-.205+.17*fall,.61-.04*fall),(.10+.75*fall,-.36-.01*fall,.93-.56*fall))
  orient_hand(rig,'R',(0,-1+.293*fall,.08-.787*fall))
  for side,sg in [('L',1),('R',-1)]:
   rotate_world(rig,'HindFemur_'+side,'X',45*fall);rotate_world(rig,'HindTibia_'+side,'X',-35*fall)
   rotate_world(rig,'MidTibia_'+side,'X',50*fall)
  rig.pose.bones['Root'].location=(0,0,0);bpy.context.view_layer.update()
  rotate_world(rig,'Root','X',-135*fall,pivot=(0,.03,.50));rotate_world(rig,'Root','Y',15*fall,pivot=(0,.03,.50))
  # Settle membranes flat after the body rolls, so their tips cannot support a floating corpse.
  if fall>.7:
   w=smooth((fall-.7)/.3)
   for side,sg in [('L',1),('R',-1)]:
    b=rig.pose.bones['WingRoot_'+side];target=Matrix.Rotation(math.pi/2,3,'X')@Matrix.Rotation(math.radians(sg*15),3,'Y')@rest[b.name].to_3x3();q=b.matrix.to_quaternion().slerp(target.to_quaternion(),w);mat=q.to_matrix().to_4x4();mat.translation=b.head;b.matrix=mat
    rig.pose.bones['WingFlex_'+side].rotation_quaternion=(1,0,0,0)
   bpy.context.view_layer.update()
 bpy.context.view_layer.update()
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());minimum=min(v.co.z for v in ev.data.vertices)
 # Root local axes have rotated in Death; location lives in the root's rest frame.
 lift=.002-minimum+.02*min(1,t/.10,max(0,(.875-t)/.05)) if role=='Death' else max(0,-minimum)
 rig.pose.bones['Root'].location+=rest['Root'].to_3x3().transposed()@Vector((0,0,lift));bpy.context.view_layer.update()
 return lift
rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
report={};saved={}
for role,dur in durations.items():
 rig.animation_data_create();action=bpy.data.actions.new(role);rig.animation_data.action=action
 frames=int(round(dur*48));lifts=[];mins=[]
 for f in range(frames+1):
  sc.frame_set(f);lifts.append(pose(role,f/48))
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=f,group=b.name);b.keyframe_insert('rotation_quaternion',frame=f,group=b.name);b.keyframe_insert('scale',frame=f,group=b.name)
  ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());mins.append(min(v.co.z for v in ev.data.vertices))
  if f in (0,frames):saved[(role,f)]=np.array([v.co[:] for v in ev.data.vertices])
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 action.use_fake_user=True;report[role]=dict(duration=dur,frames=frames+1,min_z=min(mins),maximum_floor_correction=max(lifts))
 if role in ['Fly','FlyFast','Dead']:
  error=float(np.max(np.linalg.norm(saved[(role,0)]-saved[(role,frames)],axis=1)));report[role]['loop_vertex_error']=error;assert error<1e-5,(role,error)
 assert min(mins)>-.0001,(role,min(mins))
assert np.max(np.abs(saved[('Death',42)]-saved[('Dead',0)]))<1e-6
rig.animation_data.action=bpy.data.actions['Fly'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0);sc.frame_start=0;sc.frame_end=30
(P/'work/clip_metrics.json').write_text(json.dumps(report,indent=2));print('CLIPS',json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
