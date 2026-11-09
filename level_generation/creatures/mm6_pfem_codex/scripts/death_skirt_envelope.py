"""Follow the enclosed legs during the prone fall, with independent skirt-ring transforms."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];sc=bpy.context.scene
ch=json.loads(sc['skirt_chains']);a=bpy.data.actions['Death']
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
names=[n for c in ch for n in c['bones']]
# Independent rings can compress a closed garment without chain-length buckling.
for o in bpy.data.objects:o.select_set(o==r)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for n in names:r.data.edit_bones[n].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in list(bag.fcurves):
    if 'Skirt_' in fc.data_path:bag.fcurves.remove(fc)
for n in names:r.pose.bones[n].matrix_basis.identity()
def avg(names,rest=False):
 return sum((r.data.bones[n].head_local if rest else r.pose.bones[n].head for n in names),Vector())/len(names)
joints=[['B_Pelvis'],['B_L_Thigh','B_R_Thigh'],['B_L_Calf','B_R_Calf'],['B_L_Foot','B_R_Foot']]
centres0=[avg(ns,True) for ns in joints]
# Extend waist above the pelvis using its actual rest axis.
waist0=Vector((centres0[0].x,centres0[0].y,1.055))
centres0[0]=waist0
restpel=r.data.bones['B_Pelvis'].matrix_local.copy()
source=[]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f)
 source.append(([avg(ns) for ns in joints],r.pose.bones['B_Pelvis'].matrix.copy(),
                [r.pose.bones['B_L_'+n].head-r.pose.bones['B_R_'+n].head for n in ('Thigh','Calf','Foot')]))
# Skirt translations are authored only for this fall; other actions explicitly reset them.
for other in bpy.data.actions:
 if other.name in ('Standing','Walking','Hit','Fidget'):
  r.animation_data.action=other;r.animation_data.action_slot=other.slots[0]
  for n in names:
   pb=r.pose.bones[n];pb.location=(0,0,0);pb.scale=(1,1,1)
   for frame in other.frame_range:
    pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('scale',frame=frame)
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
me=ob.data;pv=np.array([x.value for x in me.attributes['piece'].data])
ids=np.flatnonzero(pv==100);verts=np.array([me.vertices[i].co[:] for i in ids])
W=np.zeros((len(ids),len(names)));ni={n:i for i,n in enumerate(names)}
for row,i in enumerate(ids):
 for g in me.vertices[i].groups:
  n=ob.vertex_groups[g.group].name
  if n in ni:W[row,ni[n]]=g.weight
solve=np.linalg.solve(W.T@W+np.eye(len(names))*.003,W.T)
previous_positions=None
prev={}
for f,(C,pm,S) in enumerate(source):
 sc.frame_set(f);C[0]=pm@restpel.inverted()@waist0
 desired={}
 for c in ch:
  for n in c['bones']:
   b=r.data.bones[n];z=b.head_local.z
   ii=min(2,next((i for i in range(3) if z>=centres0[i+1].z),2))
   u=max(0.,min(1.,(centres0[ii].z-z)/(centres0[ii].z-centres0[ii+1].z)))
   ctr=C[ii].lerp(C[ii+1],u);ctr0=centres0[ii].lerp(centres0[ii+1],u)
   down=(C[ii+1]-C[ii]).normalized()
   side=S[max(0,ii-1)].lerp(S[ii],u);side-=down*side.dot(down);side.normalize()
   back=side.cross(down).normalized()
   R=Matrix((side,back,-down)).transposed()
   radial=b.head_local-ctr0
   offset=R@radial
   flat=max(0.,min(1.,(1-abs(down.z))*1.1))
   offset.z*=1-.60*flat
   h=ctr+offset;h.z=max(h.z,.045)
   M=(R@b.matrix_local.to_3x3()).to_4x4();M.translation=h
   desired[n]=M
 # Fit ring translations to a smooth, floor-constrained surface envelope.
 targets=[]
 for v in verts:
  z=v[2];ii=min(2,next((i for i in range(3) if z>=centres0[i+1].z),2))
  u=max(0.,min(1.,(centres0[ii].z-z)/(centres0[ii].z-centres0[ii+1].z)))
  ctr=C[ii].lerp(C[ii+1],u);ctr0=centres0[ii].lerp(centres0[ii+1],u)
  down=(C[ii+1]-C[ii]).normalized()
  side=S[max(0,ii-1)].lerp(S[ii],u);side-=down*side.dot(down);side.normalize()
  back=side.cross(down).normalized();R=Matrix((side,back,-down)).transposed()
  off=R@(Vector(v)-ctr0)
  flat=max(0.,min(1.,(1-abs(down.z))*1.1))
  off.z*=1-.60*flat
  target=ctr+off;target.z=max(target.z,.012)
  targets.append(target[:])
 targets=np.array(targets)
 def positions():
  out=np.zeros_like(verts)
  for row,i in enumerate(ids):
   v=me.vertices[i].co
   for g in me.vertices[i].groups:
    n=ob.vertex_groups[g.group].name
    M=desired[n] if n in desired else r.pose.bones[n].matrix
    out[row]+=g.weight*np.array(M@r.data.bones[n].matrix_local.inverted()@v)
  return out
 pred=positions()
 shift=solve@(targets-pred)
 for k,n in enumerate(names):desired[n].translation+=Vector(shift[k])
 # Raise only cloth control translations when interpolation would put a fold below the floor.
 for it in range(5):
  pred=positions();error=np.maximum(.006-pred[:,2],0)
  if error.max()<.001:break
  dz=solve@(error*1.15)
  for k,n in enumerate(names):desired[n].translation.z+=float(dz[k])
 # Derive local basis from desired parent matrices; no inherited simulator state.
 for c in ch:
  for n in c['bones']:
   b=r.data.bones[n];par=b.parent
   parent=desired.get(par.name,r.pose.bones[par.name].matrix.copy())
   local=(parent@par.matrix_local.inverted()@b.matrix_local).inverted()@desired[n]
   loc,q,scale=local.decompose()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb=r.pose.bones[n];pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
   for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=f)
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/skirt_animated.blend'))
print('DEATH enclosed-leg drape baked')
