"""Use a 0.2-second stance blend for the short hit; the shorter blend accelerated the off-arm above the source."""
import bpy,sys,os
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));r=bpy.data.objects['Rig'];sc=bpy.context.scene
source=P/'work'/kind/('motion_grip.blend' if kind=='male' else 'motion_run.blend')
def active(a):
 r.animation_data.action=a
 if a and a.slots:r.animation_data.action_slot=a.slots[0]
def pose(a,f):
 active(a);sc.frame_set(f);return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones if 'Twist' not in b.name}
def smooth(x):
 x=min(1,max(0,x));return x*x*(3-2*x)
for name in (('Kept_Hit','Kept_ArmedHit') if kind=='male' else ('Kept_Hit',)):
 home=pose(bpy.data.actions[name.replace('Hit','Standing')],0);old=bpy.data.actions[name]
 with bpy.data.libraries.load(str(source),link=False)as(data,to):to.actions=[name]
 raw=to.actions[0];n=int(raw.frame_range[1]);poses=[]
 for f in range(n+1):
  p=pose(raw,f);w=min(smooth(f/6),smooth((n-f)/6));poses.append({b:((home[b][0] if home[b][0].dot(q)>=0 else -home[b][0]).slerp(q,w),home[b][1].lerp(l,w))for b,(q,l) in p.items()})
 active(old);prev={}
 for f,p in enumerate(poses):
  for b,(q,l) in p.items():
   if b in prev and q.dot(prev[b])<0:q.negate()
   prev[b]=q.copy();pb=r.pose.bones[b];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
   if b=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 bpy.data.actions.remove(raw)
active(None)
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
