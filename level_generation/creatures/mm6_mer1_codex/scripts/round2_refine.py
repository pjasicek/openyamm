"""Fresh continuous-sleeve weight cleanup and limited anatomical rotation cleanup."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/textured.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene
pv=np.array([v.value for v in o.data.attributes['piece'].data]);gn={g.index:g.name for g in o.vertex_groups}
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)
def put(v,w):
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 z=sum(w.values())
 for n,x in w.items():
  if x>1e-6:o.vertex_groups[n].add([v.index],float(x/z),'REPLACE')
for v in o.data.vertices:
 if pv[v.index]!=1:continue
 sd='L'if v.co.x>0 else'R';a=r.data.bones[f'B_{sd}_UpperArm'].head_local;b=r.data.bones[f'B_{sd}_Forearm'].head_local;d=b-a;t=(v.co-a).dot(d)/d.length_squared
 w={gn[g.group]:g.weight for g in v.groups};arm=sum(x for n,x in w.items()if n.startswith(f'B_{sd}_'));keep=smooth((t-.15)/.38)*smooth((abs(v.co.x)-.20)/.095)
 axial=[n for n in w if not n.startswith(f'B_{sd}_')];move=sum(w[n]*keep for n in axial)
 for n in axial:w[n]*=1-keep
 if arm>1e-5:
  for n in list(w):
   if n.startswith(f'B_{sd}_'):w[n]+=move*w[n]/arm
 else:w[f'B_{sd}_UpperArm']=move
 put(v,w)
# Quaternion decomposition in each retained anatomical bone frame.
def cap(q,axis,twist_limit,swing_limit=180):
 q=q.normalized();q=-q if q.w<0 else q;axis=axis.normalized();v=Vector((q.x,q.y,q.z));p=axis*v.dot(axis);tw=Quaternion((q.w,*p));tw.normalize();sw=q@tw.inverted();angle=2*math.atan2(Vector((tw.x,tw.y,tw.z)).dot(axis),tw.w)
 def limit(x,m):
  z=abs(x);a=math.radians(m)*.88;b=math.radians(m)*.12
  return math.copysign(a+b*math.tanh((z-a)/b),x)if z>a else x
 tw=Quaternion(axis,limit(angle,twist_limit));sw=Quaternion(sw.axis,limit(sw.angle,swing_limit));return sw@tw
changes={}
for a in bpy.data.actions:
 if a.name=='Dead':continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];names=[f'B_{sd}_{n}'for sd in 'LR'for n in ['UpperArm','Hand']];frames=np.arange(0,float(a.frame_range[1])+.001,.25);data={n:[]for n in names};held=[]
 for f in frames:
  s.frame_set(int(f),subframe=f%1)
  held.append(r.pose.bones['B_R_Hand'].matrix.inverted()@r.pose.bones['Club'].matrix)
  for n in names:
   axis=Vector((0,1,0))
   if n.endswith('Hand'):
    sd=n[2];heads=[r.data.bones[f'B_{sd}_Finger{k}'].head_local for k in range(5)];axis=r.data.bones[n].matrix_local.to_3x3().inverted()@(sum(heads,Vector())/5-r.data.bones[n].head_local)
   q=cap(r.pose.bones[n].rotation_quaternion.copy(),axis,42 if n.endswith('Hand')else 58,66 if n.endswith('Hand')else 180);data[n].append(q)
 for n,qs in data.items():
  prev=None
  for f,q in zip(frames,qs):
   if prev and q.dot(prev)<0:q=-q
   prev=q;b=r.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f))
 # Recompute attachment from the new hand orientation while retaining its belt anchor and draw timing.
 if a.name=='Attack':
  for f,H in zip(frames,held):
   s.frame_set(int(f),subframe=f%1);w=smooth(f/6)*smooth((float(frames[-1])-f)/7.5)
   if w>.999:
    b=r.pose.bones['Club'];b.matrix=r.pose.bones['B_R_Hand'].matrix@H;b.keyframe_insert('location',frame=float(f));b.keyframe_insert('rotation_quaternion',frame=float(f))
 changes[a.name]=len(frames)
# Use the fresh maps in the existing materials; packed images otherwise retain the previous compose.
for im in bpy.data.images:
 if im.source=='FILE' and 'textures/round2/'in im.filepath:
  if im.packed_file:im.unpack(method='REMOVE')
  im.reload()
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/refined.blend'))
(P/'review/round2/rotation_cleanup.json').write_text(json.dumps(changes,indent=2))
print('CHAIN REST',s.get('merchant_skirt'))
