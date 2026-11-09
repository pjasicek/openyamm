"""Fit the tail centreline by its connected rear branch; keep its root on the pelvis."""
import bpy,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_grip.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);piece=np.array([v.value for v in me.attributes['piece'].data])
mask=(piece==0)&(co[:,1]>.285);edges=np.array([e.vertices[:] for e in me.edges]);adj={i:[] for i in np.where(mask)[0]}
for a,b in edges[mask[edges[:,0]]&mask[edges[:,1]]]:adj[a].append(b);adj[b].append(a)
stack=[int(np.argmax(co[:,1]))];seen=set()
while stack:
 i=stack.pop()
 if i in seen:continue
 seen.add(i);stack.extend(adj.get(i,[]))
ids=np.array(sorted(seen));P=co[ids];assert len(ids)>200
centers=[]
for y in np.linspace(P[:,1].min(),P[:,1].max(),8):
 band=P[abs(P[:,1]-y)<.035]
 centers.append(band.mean(0))
centers=np.array(centers);centers[0]=[-.035,.26,1.00];centers[-1]=P[np.argmax(np.linalg.norm(P-centers[0],axis=1))]
assert np.all(np.isfinite(centers))
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i in range(len(centers)-1):
 b=rig.data.edit_bones.new('Tail'+str(i));b.head=Vector(centers[i]);b.tail=Vector(centers[i+1]);b.parent=rig.data.edit_bones['Tail'+str(i-1)] if i else rig.data.edit_bones['B_Pelvis'];b.align_roll(Vector((0,0,1)))
bpy.ops.object.mode_set(mode='OBJECT')
# The tail grows from the pelvis, so its surrounding buttock skin cannot follow opposite thighs.
for v in me.vertices:
 if piece[v.index]!=0:continue
 q=co[v.index];t=float(np.clip((q[1]-.15)/.14,0,1)*np.clip((q[2]-.72)/.14,0,1))
 if t<=0:continue
 moved=0
 for g in list(v.groups):
  name=body.vertex_groups[g.group].name
  if any(x in name for x in ('Thigh','Calf','Foot','Toe')):
   moved+=g.weight*t;body.vertex_groups[g.group].add([v.index],g.weight*(1-t),'REPLACE')
 if moved:body.vertex_groups['B_Pelvis'].add([v.index],moved,'ADD')
ng=[body.vertex_groups.new(name='Tail'+str(i)) for i in range(len(centers)-1)]
for vi in ids:
 q=co[vi];best=(1e9,0,0)
 for i,(a,b) in enumerate(zip(centers[:-1],centers[1:])):
  t=float(np.clip((q-a)@(b-a)/((b-a)@(b-a)),0,1));d=np.linalg.norm(q-a-t*(b-a))
  if d<best[0]:best=(d,i,t)
 _,i,t=best
 for g in body.vertex_groups:g.remove([int(vi)])
 if i==0:
  into=float(np.clip((q[1]-.285)/.08,0,1));body.vertex_groups['B_Pelvis'].add([int(vi)],1-into,'REPLACE')
 else:into=1
 a=max(0,min(1,(t-.5)+.5));j=min(i+1,len(ng)-1)
 ng[i].add([int(vi)],into*(1-a),'REPLACE');ng[j].add([int(vi)],into*a,'ADD')
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act
 if len(act.slots):rig.animation_data.action_slot=act.slots[0]
 n=int(act.frame_range[1])
 for f in range(n+1):
  bpy.context.scene.frame_set(f)
  amp=math.radians(2 if act.name in ('Standing','Fidget') else 4)
  if act.name=='Death':amp*=max(0,1-f/max(n,1))
  for i in range(len(ng)):
   pb=rig.pose.bones['Tail'+str(i)];pb.rotation_mode='QUATERNION';phase=math.tau*f/max(n,1)-i*.42
   pb.rotation_quaternion=Quaternion((0,0,1),amp*math.sin(phase))
   pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
json.dump({'vertices':ids.tolist(),'centers':centers.tolist(),'chain_length_m':float(np.linalg.norm(np.diff(centers,axis=0),axis=1).sum())},open(p/'work/tail_fit.json','w'),indent=2)
print('TAIL',len(ids),'vertices',centers.tolist())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_tail.blend'))
