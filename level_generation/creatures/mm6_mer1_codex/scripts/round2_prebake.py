"""Final pre-bake cleanup; retain the accepted smooth library fall's cloth response."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));body=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene;part=np.array([a.value for a in body.data.attributes['piece'].data]);co=np.array([v.co[:]for v in body.data.vertices]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(names)));adj=[[]for _ in co]
for v in body.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
for e in body.data.edges:
 a,b=e.vertices
 if part[a]==part[b]==1:adj[a].append(b);adj[b].append(a)
for _ in range(32):
 old=W.copy()
 for i,nb in enumerate(adj):
  if nb and abs(co[i,0])>.16 and co[i,2]>.97:W[i]=.65*old[i]+.35*old[nb].mean(0)
for v in body.data.vertices:
 if part[v.index]!=1:continue
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 ids=np.argsort(W[v.index])[-4:];total=W[v.index,ids].sum()
 for gi in ids:
  if W[v.index,gi]>1e-7:body.vertex_groups[int(gi)].add([v.index],float(W[v.index,gi]/total),'REPLACE')
 sd='L'if v.co.x>0 else'R';wr=r.data.bones[f'B_{sd}_Hand'].head_local;axis=(wr-r.data.bones[f'B_{sd}_Forearm'].head_local).normalized();d=v.co-wr;z=d.dot(axis);radius=d-axis*z;t=max(0,1-abs(z)/.045)
 if t and abs(v.co.x)>.4 and radius.length>.005:v.co+=radius.normalized()*(.007*t)
# Restore only the already-smoothed cloth channels from the accepted source fall.
original=bpy.data.actions['Death'];with_names=set(bpy.data.actions)
with bpy.data.libraries.load(str(P/'work/reduction_master.blend'),link=False)as(src,dst):dst.actions=['Death']
src=dst.actions[0];r.animation_data.action=src;r.animation_data.action_slot=src.slots[0];frames=np.arange(0,float(src.frame_range[1])+.001,.25);data=[];cloth=[b for b in r.pose.bones if b.name.startswith('Cloak_')]
for f in frames:
 s.frame_set(int(f),subframe=f%1);data.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in cloth})
r.animation_data.action=original;r.animation_data.action_slot=original.slots[0]
for l in original.layers:
 for st in l.strips:
  for cb in st.channelbags:
   for fc in list(cb.fcurves):
    if 'Cloak_'in fc.data_path:cb.fcurves.remove(fc)
for f,row in zip(frames,data):
 for n,(q,v)in row.items():b=r.pose.bones[n];b.rotation_quaternion=q;b.location=v;b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
bpy.data.actions.remove(src)
s.frame_set(int(frames[-1]),subframe=frames[-1]%1);terminal={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in [0,30]:
 for b in r.pose.bones:
  b.matrix_basis=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Capture actual new hand-plane normals for the shared checks.
palms={}
for sd in 'LR':
 h=r.data.bones[f'B_{sd}_Hand'];v1=r.data.bones[f'B_{sd}_Finger1'].head_local-h.head_local;v4=r.data.bones[f'B_{sd}_Finger4'].head_local-h.head_local;n=v1.cross(v4).normalized()*(1 if sd=='R'else -1);palms[sd]=list(h.matrix_local.to_3x3().inverted()@n)
(P/'work/round2/palm_normals.json').write_text(json.dumps(palms,indent=2));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/master.blend'))
