import bpy,math
from mathutils import Vector,Matrix,Quaternion
r=None;B=None;names=None;previous={}
def init(rig):
 global r,B,names
 r=rig;B=r.data.bones;names=[b.name for b in B]
def update():bpy.context.view_layer.update()
def setact(a):
 r.animation_data_create();r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def capture():return {n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 setact(None)
 for n,(q,l) in pose.items():r.pose.bones[n].rotation_mode='QUATERNION';r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].location=l
 update()
def worldrot(n,q):
 pb=r.pose.bones[n];m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;update()
def basis(a,b):
 a=Vector(a).normalized();b=Vector(b);b=(b-a*b.dot(a)).normalized();return Matrix((a,b,a.cross(b))).transposed()
def aim(n,c,target):
 pb=r.pose.bones[n];rest=B[c].head_local-B[n].head_local;carry=pb.parent.matrix.to_3x3()@B[n].parent.matrix_local.to_3x3().inverted() if pb.parent else Matrix.Identity(3)
 worldrot(n,(carry@rest).rotation_difference(Vector(target)-pb.head)@(carry@B[n].matrix_local.to_3x3()).to_quaternion())
def chain(sd,target,pole,leg=False):
 u,f,h=[f'B_{sd}_{n}' for n in (['Thigh','Calf','Foot'] if leg else ['UpperArm','Forearm','Hand'])];sh=r.pose.bones[u].head.copy();L1=(B[f].head_local-B[u].head_local).length;L2=(B[h].head_local-B[f].head_local).length
 dv=Vector(target)-sh;D=min(dv.length,L1+L2-.001);d=dv.normalized();target=sh+d*D;a=(L1*L1-L2*L2+D*D)/(2*D);b=math.sqrt(max(0,L1*L1-a*a));v=Vector(pole)-sh;v=(v-d*v.dot(d)).normalized();el=sh+d*a+v*b
 if leg:aim(u,f,el);aim(f,h,target)
 else:
  ur=B[f].head_local-B[u].head_local;fr=B[h].head_local-B[f].head_local;nr=ur.cross(Vector((0,-1,0))).normalized()
  parent=r.pose.bones[u].parent.matrix@B[u].parent.matrix_local.inverted()@B[u].matrix_local
  axis=(B[u].matrix_local.inverted()@B[f].head_local).normalized();best=None
  # Pick the nearest elbow plane with an anatomical humeral roll, retaining fixed segment lengths.
  for degrees in range(-180,181,1):
   v2=Quaternion(d,math.radians(degrees))@v;e2=sh+d*a+v2*b;u2=(e2-sh).normalized();f2=(target-e2).normalized();n2=u2.cross(f2).normalized()
   q=(basis(u2,n2)@basis(ur,nr).transposed()).to_quaternion()@B[u].matrix_local.to_quaternion();lq=parent.to_quaternion().inverted()@q
   twist=math.degrees(2*math.atan2(Vector((lq.x,lq.y,lq.z)).dot(axis),lq.w));twist=(twist+180)%360-180
   cost=.2*abs(degrees)+1000*max(0,abs(twist)-48)+200*max(0,(-1 if sd=='R' else 1)*(sh.x-e2.x)-.025)
   if sd in previous:cost+=25*min(math.degrees(previous[sd].rotation_difference(q).angle),360-math.degrees(previous[sd].rotation_difference(q).angle))
   if best is None or cost<best[0]:best=(cost,e2)
  el=best[1];up=(el-sh).normalized();fo=(target-el).normalized();normal=up.cross(fo).normalized()
  worldrot(u,(basis(up,normal)@basis(ur,nr).transposed()).to_quaternion()@B[u].matrix_local.to_quaternion())
  worldrot(f,(basis(fo,normal)@basis(fr,nr).transposed()).to_quaternion()@B[f].matrix_local.to_quaternion());previous[sd]=r.pose.bones[u].matrix.to_quaternion().copy()
 assert (r.pose.bones[h].head-target).length<.0002
def smooth(t):t=min(1,max(0,t));return t*t*(3-2*t)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in a}
def write(name,frames):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 act=bpy.data.actions.new(name);act.use_fake_user=True;setact(act);prev={}
 for i,pose in enumerate(frames):
  for n,(q,l) in pose.items():
   q=q.copy()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=i)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(frames)-1;setact(None)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return act
