"""Complete the source action set on the reviewed pilot rig; keep inferred depth explicit."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import author_pilots as P
from mathutils import Vector,Quaternion,Matrix
import bpy

P.TRACKS['Hit']=dict(rootz=[-.012,-.022,-.025,-.039,-.025,-.011,-.008],rootx=[.082,.091,.094,.088,.084,.082,.082],yaw=[-25,-42,-35,-10,-4,0,0],lean=[-5,-10,5,18,12,3,0],sidelean=[-5,-12,-12,-3,-2,0,0],headpitch=[0,5,22,29,18,6,3],headyaw=[-20,-28,-20,-5,-2,0,0],Rdepth=[-.13,-.17,-.23,-.25,-.24,-.15,-.105],Ldepth=[-.20,-.38,-.34,-.32,-.20,-.07,-.025],freecurl=[8,4,6,12,14,16,16],fan=[9,12,7,4,4,2,2],jaw=[2,4,3,2,1,0,0],rollR=[-12,-25,-10,10,12,8,8],plane=[(1,0,0)]*7,freelong=[(-.65,-.3,.45),(-1,-.2,.05),(-.35,-.25,.85),(.05,-.1,.9),(.1,-.1,.85),(0,-.1,-1),(0,-.1,-1)],freepalm=[(-.3,-1,0),(.2,-1,.1),(-.1,-1,.1),(-.2,-1,0),(-.5,-.8,0),(-1,-.05,0),(-1,-.05,0)])
blade=[]
for anchor in P.CLIPS['Hit']['anchors']:
 w,t=anchor['points_xy'][4],anchor['points_xy'][13];x=(t[0]-w[0])*1.65/256/P.BLADE_LENGTH;z=(w[1]-t[1])*1.65/256/P.BLADE_LENGTH
 length=math.hypot(x,z)
 if length>.97:x*=.97/length;z*=.97/length
 blade.append((x,-math.sqrt(max(.035,1-x*x-z*z)),z))
P.TRACKS['Hit']['blade']=blade+[P.TRACKS['Standing']['blade'][0]]
P.TRACKS['Fidget']={k:v*7 for k,v in P.TRACKS['Standing'].items()}
P.TRACKS['Fidget']['freecurl']=[16,17,19,20,18,17,16]
P.TRACKS['Fidget']['fan']=[2,2,3,3,2,2,2]
P.TRACKS['Fidget']['lean']=[0,.10,.22,.25,.12,0,0]

# Interpolate full palm orientations: opposite finger vectors must never pass through zero.
P.pose('Standing',0)
standing_left=P.arm.pose.bones['LeftHand'].matrix.to_quaternion().copy()
baseline=Matrix((Vector((0,-1,0)),Vector((0,0,-1)),Vector((1,0,0)))).transposed()
qs=[]
for direction,palm in zip(P.TRACKS['Hit']['freelong'][:6],P.TRACKS['Hit']['freepalm'][:6]):
 long=Vector(direction).normalized();normal=Vector(palm);normal=(normal-long*normal.dot(long)).normalized();across=-long.cross(normal).normalized();normal.negate()
 q=(Matrix((across,long,normal)).transposed()@baseline.transposed()@P.REST['LeftHand'].to_3x3()).to_quaternion()
 if qs and qs[-1].dot(q)<0:q.negate()
 qs.append(q)
if qs[-1].dot(standing_left)<0:standing_left.negate()
P.LEFT_ORIENTATIONS['Hit']=qs+[standing_left]

original_pose=P.pose
death=dict(rootz=[-.035,-.17,-.33,-.64,-.638,-.64],rooty=[0,0,.12,.35,.35,.35],hippitch=[5,12,60,90,90,90],lean=[18,38,20,0,.8,0],headpitch=[24,20,10,8,8.8,8],roll=[0,0,3,14,14,14],Rdepth=[-.14,-.23,-.25,-.22,-.22,-.22],Ldepth=[-.12,-.23,-.30,-.13,-.13,-.13])
death_wrist={side:[P.wrist_xy('Death',i,side) for i in range(3)]+[(-.48,.11) if side=='Right' else (.62,.085)]*3 for side in ['Right','Left']}
death_blade=[]
for i in range(6):
 anchor=P.CLIPS['Death']['anchors'][min(i,4)];tip=anchor['points_xy'][13];x,z=death_wrist['Right'][i]
 bx=((tip[0]-177.5)*1.65/256-x)/P.BLADE_LENGTH;bz=((289-tip[1])*1.65/256-z)/P.BLADE_LENGTH
 assert bx*bx+bz*bz<1,'Native blade projection exceeds fixed prop length'
 death_blade.append((bx,-math.sqrt(1-bx*bx-bz*bz),bz))

def cap(side):
 suffix='R' if side=='Right' else 'L';parent=P.arm.pose.bones[side+'Shoulder'];pd=parent.matrix.to_quaternion()@P.REST[parent.name].to_quaternion().inverted();ld=P.arm.pose.bones[side+'Arm'].matrix.to_quaternion()@P.REST[side+'Arm'].to_quaternion().inverted()
 P.assign('ArmorShoulder.'+suffix,pd@Quaternion().slerp(pd.inverted()@ld,.28)@P.REST['ArmorShoulder.'+suffix].to_quaternion())

def death_sample(values,phase):
 value=P.sample(values,phase);i=min(len(values)-1,max(0,int(math.floor(phase))));j=min(len(values)-1,i+1)
 if isinstance(value,Vector):return Vector([max(min(values[i][k],values[j][k]),min(max(values[i][k],values[j][k]),value[k])) for k in range(len(value))])
 return max(min(values[i],values[j]),min(max(values[i],values[j]),value))

def death_leg(side,target,pole):
 first=side+'UpLeg';second=side+'Leg';last=side+'Foot';tip=P.chain(first,second,target,pole,last)
 hip_delta=P.arm.pose.bones['Hips'].matrix.to_quaternion()@P.REST['Hips'].to_quaternion().inverted()
 av=P.REST[second].translation-P.REST[first].translation;bv=P.REST[last].translation-P.REST[second].translation
 a=P.arm.pose.bones[first].head.copy();k=P.arm.pose.bones[second].head.copy()
 q=(hip_delta@av).normalized().rotation_difference((k-a).normalized())@hip_delta@P.REST[first].to_quaternion();P.assign(first,q)
 delta=q@P.REST[first].to_quaternion().inverted();P.assign(second,(delta@bv).normalized().rotation_difference((tip-k).normalized())@delta@P.REST[second].to_quaternion())

def death_pose(phase):
 P.reset();c={k:death_sample(v,phase) for k,v in death.items()};root=P.arm.pose.bones['Hips'];root.matrix=Matrix.Translation((.082,c['rooty'],c['rootz']))@root.matrix;P.update()
 P.rotate('Hips',(1,0,0),c['hippitch']);P.rotate('Hips',(0,1,0),c['roll'])
 for name,share in [('Spine02',.25),('Spine01',.35),('Spine',.40)]:P.rotate(name,(1,0,0),c['lean']*share)
 P.rotate('Head',(1,0,0),c['headpitch'])
 for side in ['Right','Left']:
  x,z=death_sample(death_wrist[side],phase);target=Vector((x,c['Rdepth' if side=='Right' else 'Ldepth'],z));pole=(-.30 if side=='Right' else .50,-.10,.24 if phase>2 else .75)
  P.chain(side+'Arm',side+'ForeArm',target,pole,side+'Hand')
  if side=='Right':P.hand(side,death_sample(death_blade,phase),plane=death_sample([(0,-1,0),(0,-1,0),(0,-1,-.25),(0,0,-1),(0,0,-1),(0,0,-1)],phase),roll=5)
  else:
   blend=max(0,min(1,phase-1));direction=Vector((0,-.1,-1)).lerp(Vector((1,0,-.08)),blend);palm=Vector((-1,0,0)).lerp(Vector((0,0,-1)),blend)
   P.hand(side,curl=death_sample([14,12,6,3,3,3],phase),fan=5,direction=direction,palm=palm,roll=0)
  if side=='Left':
   P.update();mesh=P.body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
   ids=[v.index for v in P.body.data.vertices if any(P.body.vertex_groups[g.group].name.startswith(('LeftHand','Digit.L.')) and g.weight>.5 for g in v.groups)]
   lowest=min(mesh.vertices[i].co.z for i in ids)
   if lowest<.006:
    target.z+=.006-lowest;P.chain(side+'Arm',side+'ForeArm',target,pole,side+'Hand');P.hand(side,curl=death_sample([14,12,6,3,3,3],phase),fan=5,direction=direction,palm=palm,roll=0)
  cap(side)
 for side in ['Right','Left']:
  foot=P.REST[side+'Foot'].translation;pitch=death_sample([0,0,15,150,150,150],phase);rot=Quaternion((1,0,0),math.radians(pitch));contact=min((rot@v).z for v in P.SOLES[side]);y=foot.y+death_sample([0,0,.07,1.15,1.15,1.15],phase)
  target=Vector((foot.x+.082,y,.006-contact));pole=(foot.x+.082+(-.05 if side=='Right' else .05),.60,.36)
  death_leg(side,target,pole);P.assign(side+'Foot',rot@P.REST[side+'Foot'].to_quaternion())
  ids=[v.index for v in P.body.data.vertices if any(P.body.vertex_groups[g.group].name in [side+'Leg',side+'Foot'] and g.weight>.8 for g in v.groups)]
  for _ in range(5):
   P.update();mesh=P.body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;minimum=min(mesh.vertices[i].co.z for i in ids)
   if minimum>=.006:break
   target.z+=.009-minimum;death_leg(side,target,pole);P.assign(side+'Foot',rot@P.REST[side+'Foot'].to_quaternion())
 hip_delta=P.arm.pose.bones['Hips'].matrix.to_quaternion()@P.REST['Hips'].to_quaternion().inverted()
 for i in range(12):
  name=f'Skirt.{i:02d}';bone=P.arm.pose.bones[name];phi=-math.pi+(i+.5)*math.tau/12;axis=Vector((math.cos(phi),math.sin(phi),0))
  bend=math.radians(6);verts=[v.co for v in P.body.data.vertices if any(P.body.vertex_groups[g.group].name==name and g.weight>.99 for g in v.groups)]
  def rotation(angle):return hip_delta@Quaternion(axis,-angle)@P.REST[name].to_quaternion()
  def lowest(angle):
   transform=Matrix.Translation(bone.head)@rotation(angle).to_matrix().to_4x4()@P.REST[name].inverted()
   return min((transform@v).z for v in verts)
  if lowest(bend)<.006:
   sign=1 if lowest(bend+.15)>lowest(bend-.15) else -1;low=0;high=1.15
   if lowest(bend+sign*high)<.006:raise ValueError(('leather floor clearance',phase,i))
   for _ in range(18):
    mid=(low+high)/2
    if lowest(bend+sign*mid)<.006:low=mid
    else:high=mid
   bend+=sign*high
  P.assign(name,rotation(bend))
 P.update()

def pose(clip,phase):
 if clip in ['Death','Corpse']:
  death_pose(3 if clip=='Corpse' else phase);return
 original_pose(clip,phase)
 if clip=='Hit':
  lift=P.sample([0,.11,.025,0,0,0,0],phase);P.foot('Left',-.035*(1-min(1,max(0,phase-5))),lift,-5*min(1,lift/.08));P.skirt_follow();P.update()

P.pose=pose
P.build([('Standing',6),('Walk',36),('Attack',36),('Hit',36),('Death',30),('Corpse',6),('Fidget',36)],'native_full_v1.blend')
# Dense authored keys around the collapse keep measured surface contacts through fast foot rotations.
a=bpy.data.actions['Death'];P.arm.animation_data.action=a;P.arm.animation_data.action_slot=a.slots[0]
for i in range(121):
 frame=1+i/4;bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));death_pose((frame-1)/6)
 for bone in P.arm.pose.bones:
  bone.keyframe_insert('location',frame=frame,group=bone.name);bone.keyframe_insert('rotation_quaternion',frame=frame,group=bone.name)
for bag in a.layers[0].strips[0].channelbags:
 for fc in bag.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='LINEAR'
for action in bpy.data.actions:
 if action.name in P.CLIPS:action['native_duration_ms']=125 if action.name in ['Standing','Corpse'] else 625 if action.name=='Death' else 750
bpy.ops.wm.save_as_mainfile(filepath=str(P.OUT/'work/native_full_v1.blend'))
(P.OUT/'review/full_authoring.json').write_text(json.dumps({'death_drivers':death,'death_depth_confidence':'inferred from one genuine front view; prone contacts solved in 3D','native_clips':list(P.CLIPS),'status':'authored_unverified'},indent=2)+'\n')
