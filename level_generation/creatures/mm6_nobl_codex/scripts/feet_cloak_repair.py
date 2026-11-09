"""Repair boot rigidity/contact and the overlapping upper-cloak layers on revision 10."""
import bpy,numpy as np,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([v.co[:] for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
def smooth(x,a,b):
 t=float(np.clip((x-a)/(b-a),0,1));return t*t*(3-2*t)
def weights(i,w):
 for g in list(me.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 total=sum(w.values())
 for n,v in w.items():
  if v>1e-6:o.vertex_groups[n].add([i],v/total,'REPLACE')
for i in np.flatnonzero((pv==2)&(co[:,2]<.26)):
 i=int(i);side='L' if co[i,0]>0 else 'R';t=smooth(co[i,2],.13,.26)
 old={o.vertex_groups[g.group].name:g.weight*t for g in me.vertices[i].groups}
 n=f'B_{side}_Foot';old[n]=old.get(n,0)+1-t;weights(i,old)
# The mantle and cloak underneath share one chest/shoulder field; neck flex only reaches the upright collar.
cape=np.flatnonzero(pv==0)
for i in cape:
 i=int(i);x,y,z=co[i]
 if z<1.10:continue
 old={o.vertex_groups[g.group].name:g.weight for g in me.vertices[i].groups}
 arm=.7*smooth(abs(x),.17,.33)
 neck=smooth(z,1.485,1.535)*(1-smooth(abs(x),.075,.12))
 side='L' if x>0 else 'R'
 new={'B_Spine2':(1-arm)*(1-neck),f'B_{side}_UpperArm':arm*(1-neck),'B_Neck':neck}
 t=smooth(z,1.10,1.20)
 w={k:v*(1-t) for k,v in old.items()}
 for k,v in new.items():w[k]=w.get(k,0)+v*t
 weights(i,w)
# Braided edge ornaments follow the repaired cloth beneath them.
from mathutils.kdtree import KDTree
kd=KDTree(len(cape))
for i in cape:kd.insert(Vector(co[i]),int(i))
kd.balance()
for i in np.flatnonzero(np.isin(pv,[28,*range(31,109),111,115])&(co[:,2]>1.22)):
 loc,j,d=kd.find(Vector(co[i]))
 if d<.03:weights(int(i),{o.vertex_groups[g.group].name:g.weight for g in me.vertices[j].groups})
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
soles={s:np.flatnonzero((pv==2)&(co[:,2]<.006)&(co[:,0]*(1 if s=='L' else -1)>0)) for s in 'LR'}
boots={s:np.flatnonzero((pv==2)&(co[:,2]<.13)&(co[:,0]*(1 if s=='L' else -1)>0)) for s in 'LR'}
def setact(a):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def key(b,f,location=False):
 b.keyframe_insert('rotation_quaternion',frame=f)
 if location:b.keyframe_insert('location',frame=f)
def worldpose(n,M):
 b=r.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n] if b.parent else rest[n];local=base.inverted()@M
 b.rotation_mode='QUATERNION';b.rotation_quaternion=local.to_quaternion();b.location=local.translation;bpy.context.view_layer.update()
def align(n,child,head,tail):
 b=r.pose.bones[n];M=b.matrix.copy();old=(r.pose.bones[child].head-b.head).normalized();D=old.rotation_difference((tail-head).normalized())
 M=(D.to_matrix()@M.to_3x3()).to_4x4();M.translation=head;worldpose(n,M)
# Normalize quaternion signs before sampling the source clips between their 30 Hz keys.
for act in bpy.data.actions:
 curves={}
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
 for components in curves.values():
  if len(components)!=4:continue
  keys=[components[j].keyframe_points for j in range(4)];prev=None
  for k in range(min(map(len,keys))):
   q=np.array([keys[j][k].co.y for j in range(4)])
   if prev is not None and prev@q<0:
    for j in range(4):
     keys[j][k].co.y*=-1;keys[j][k].handle_left.y*=-1;keys[j][k].handle_right.y*=-1
    q=-q
   prev=q
  for fc in components.values():fc.update()
report={}
for name in ['Standing','Fidget','Walking','Running','Attack','Hit','Death']:
 a=bpy.data.actions[name];setact(a);N=int(a.frame_range[1])
 original=[]
 for step in range(N*4+1):
  f=step/4;sc.frame_set(int(f),subframe=f%1);original.append({b.name:b.matrix_basis.copy() for b in r.pose.bones})
 rows=[]
 for step in range(N*4+1):
  f=step/4;sc.frame_set(int(f),subframe=f%1)
  for b in r.pose.bones:b.matrix_basis=original[step][b.name]
  bpy.context.view_layer.update()
  targets={};rotations={};floor={}
  # On the fall, retain the authored leg pose after the brief standing anticipation.
  influence=1-smooth(f,1,8) if name=='Death' else 1
  for s in 'LR':
   n=f'B_{s}_Foot';b=r.pose.bones[n];M=b.matrix.copy();D=(M@rest[n].inverted()).to_3x3()
   forward=D@Vector((0,-1,0));yaw=math.atan2(forward.x,-forward.y)
   pitch=0.;lift=0.
   if name in ['Walking','Running']:
    # Source gait: left heel strike at 3/4 cycle; right heel strike at 1/4.
    phase=((f/N)-(.75 if s=='L' else .25))%1
    contact=.56 if name=='Walking' else .43
    pitch=-12*(1-smooth(phase,0,.09))+30*smooth(phase,contact-.13,contact)
    if phase>contact:
     t=(phase-contact)/(1-contact);pitch=30*(1-smooth(t,0,.42))-12*smooth(t,.65,1)
     lift=(.085 if name=='Walking' else .14)*math.sin(math.pi*t)**2
   # Remove lateral ankle roll; retain heading and natural heel-strike/toe-off pitch.
   R=Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(math.radians(pitch),3,'X')
   ankle=b.head.copy()
   P=(co[boots[s]]-np.array(rest[n].translation))@np.array(R).T
   ankle.z=.001+lift-float(P[:,2].min())
   targets[s]=b.head.lerp(ankle,influence)
   rotations[s]=D.to_quaternion().slerp(R.to_quaternion(),influence).to_matrix()
   if name=='Death':
    posed=(co[boots[s]]-np.array(rest[n].translation))@np.array(rotations[s]).T
    targets[s].z=max(targets[s].z,.001-float(posed[:,2].min()))
   floor[s]={'lift':lift,'pitch':pitch}
  # Lower the pelvis only when the grounded ankle is outside the leg's reach.
  drop=0.
  for s in 'LR':
   hip=r.pose.bones[f'B_{s}_Thigh'].head;ankle=targets[s]
   l1=(rest[f'B_{s}_Calf'].translation-rest[f'B_{s}_Thigh'].translation).length
   l2=(rest[f'B_{s}_Foot'].translation-rest[f'B_{s}_Calf'].translation).length
   dxy=(hip.x-ankle.x)**2+(hip.y-ankle.y)**2
   reach=math.sqrt(max(.001,(l1+l2-.003)**2-dxy))
   drop=max(drop,hip.z-ankle.z-reach)
  drop=max(0,drop)*influence
  pelvis=r.pose.bones['B_Pelvis'];M=pelvis.matrix.copy();M.translation.z-=drop;worldpose(pelvis.name,M);key(pelvis,f,True)
  for s in 'LR':
   
   tn,cn,fn=[f'B_{s}_{k}' for k in ['Thigh','Calf','Foot']]
   H=r.pose.bones[tn].head.copy();K=r.pose.bones[cn].head.copy();A=targets[s]
   l1=(rest[cn].translation-rest[tn].translation).length;l2=(rest[fn].translation-rest[cn].translation).length
   axis=(A-H).normalized();d=(A-H).length;along=(l1*l1-l2*l2+d*d)/(2*d)
   pole=(r.pose.bones['B_Pelvis'].matrix@rest['B_Pelvis'].inverted()).to_3x3()@Vector((.12 if s=='L' else -.12,-1,0))
   pole=(K-H).normalized().lerp(pole,influence) if name=='Death' else pole
   bend=pole-axis*pole.dot(axis)
   if bend.length<1e-5:bend=Vector((0,-1,0))-axis*axis.dot(Vector((0,-1,0)))
   bend.normalize();Knew=H+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))
   align(tn,cn,H,Knew);align(cn,fn,Knew,A)
   M=(rotations[s]@rest[fn].to_3x3()).to_4x4();M.translation=A;worldpose(fn,M)
   # Rigid shoe sole; keep the unused toe joint aligned for export consumers.
   toe=f'B_{s}_Toe0';D=M@rest[fn].inverted();worldpose(toe,D@rest[toe])
   for n in [tn,cn,fn,toe]:key(r.pose.bones[n],f,True)
   assert (r.pose.bones[fn].head-A).length<1e-5
  rows.append({'frame':f,'pelvis_drop_mm':drop*1000,'feet':floor})
 report[name]=rows
# Corpse keeps the corrected final fall pose.
a=bpy.data.actions['Death'];setact(a);sc.frame_set(int(a.frame_range[1]));held={b.name:b.matrix_basis.copy() for b in r.pose.bones}
a=bpy.data.actions['Dead'];setact(a)
for f in [0,30]:
 for b in r.pose.bones:b.matrix_basis=held[b.name];key(b,f,True)
a.use_frame_range=True;a.frame_start=0;a.frame_end=30
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v11_geometry.blend'))
(p/'review/feet_cloak_20261011/repair.json').write_text(json.dumps(report,indent=1))
print('REPAIR',json.dumps({k:max(r['pelvis_drop_mm'] for r in v) for k,v in report.items()}))
