"""Put the knuckle bow on the finger side and remove the taunt's crossed-arm entry."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_contacts.blend'))
rig=bpy.data.objects['Rig'];o=bpy.data.objects['CutlassMesh'];inv=rig.data.bones['Sword'].matrix_local.inverted();M=inv.inverted();co=np.array([(inv@v.co)[:] for v in o.data.vertices])
nb=[[] for v in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;nb[a].append(b);nb[b].append(a)
seen=set();bow=[]
for i in range(len(co)):
 if i in seen:continue
 stack=[i];component=[];seen.add(i)
 while stack:
  k=stack.pop();component.append(k)
  for j in nb[k]:
   if j not in seen:seen.add(j);stack.append(j)
 pts=co[component]
 if pts[:,0].min()<-.08 and pts[:,1].max()<.13 and pts[:,1].min()>-.09:bow.extend(component)
assert 60<=len(bow)<=100,len(bow)
for i in bow:
 v=inv@o.data.vertices[i].co;oldx=v.x;v.x=-v.x;v.z=-v.z;v.y+=oldx*float(np.clip((v.y+.04)/.12,0,1));o.data.vertices[i].co=M@v
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free()
sc=bpy.context.scene;st=bpy.data.actions['Standing'];rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];sc.frame_set(0)
start={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
a=bpy.data.actions['Fidget'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(24)
end={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
for f in np.arange(0,24.001,.25):
 t=f/24;t=t*t*(3-2*t)
 for b in rig.pose.bones:
  q,l=start[b.name];q1,l1=end[b.name];b.rotation_quaternion=q.slerp(q1,t);b.location=l.lerp(l1,t);b.keyframe_insert('rotation_quaternion',frame=float(f))
  if b.name=='B_Pelvis':b.keyframe_insert('location',frame=float(f))
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_delivery.blend'));print('BOW',len(bow),'FIDGET entry .8s')
