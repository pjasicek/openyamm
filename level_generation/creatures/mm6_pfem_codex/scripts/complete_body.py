"""Complete the hidden thigh surfaces and match neckline weights across the skin/cloth seam."""
import bpy,bmesh,sys,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/all_body.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bm=bmesh.new();bm.from_mesh(me);la=bm.verts.layers.int['piece'];newfaces=[]
for side,part in [('L',10),('R',8)]:
 es={e for e in bm.edges if e.is_boundary and all(v[la]==part and v.co.z>.50 for v in e.verts)}
 assert es,(side,'missing thigh opening')
 e=es.pop();ring=list(e.verts);last=ring[-1]
 while last!=ring[0]:
  e=next((e for e in last.link_edges if e in es),None)
  if e is None:break
  es.remove(e);last=e.other_vert(last)
  if last!=ring[0]:ring.append(last)
 assert last==ring[0],(side,'open loop')
 c=sum((v.co for v in ring),Vector())/len(ring);rad=[v.co-c for v in ring]
 hip=r.data.bones[f'B_{side}_Thigh'].head_local
 prev=ring
 for z,scale in [(.59,1.15),(.69,1.4),(.81,1.6),(.93,1.45)]:
  u=(z-c.z)/(.93-c.z);ctr=c.lerp(hip,u);ctr.z=z
  nr=[]
  for d in rad:
   v=bm.verts.new(ctr+Vector((d.x*scale,d.y*scale,0)));v[la]=part;nr.append(v)
  for j in range(len(ring)):newfaces.append(bm.faces.new((prev[j],prev[(j+1)%len(ring)],nr[(j+1)%len(ring)],nr[j])))
  prev=nr
 newfaces.append(bm.faces.new(prev))
for f in newfaces:f.smooth=True
bmesh.ops.triangulate(bm,faces=newfaces)
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if all(v[la] in (8,10) for v in f.verts)])
bm.to_mesh(me);bm.free()
def sm(x,a,b):
 t=np.clip((x-a)/(b-a),0,1);return float(t*t*(3-2*t))
def mix(a,b,t):
 w={n:v*(1-t) for n,v in a.items()}
 for n,v in b.items():w[n]=w.get(n,0)+v*t
 return w
def torso(z):
 knots=[1.06,1.15,1.24,1.30];ns=['B_Pelvis','B_Spine','B_Spine1','B_Spine2']
 for i in range(3):
  if z<=knots[i+1]:return mix({ns[i]:1},{ns[i+1]:1},sm(z,knots[i],knots[i+1]))
 return {ns[-1]:1}
for v in me.vertices:
 part=me.attributes['piece'].data[v.index].value;x,y,z=v.co;s='L' if x>0 else 'R'
 if part==1:
  w=mix(torso(z),{'B_Neck':1},sm(z,1.325,1.38));w=mix(w,{'B_Head':1},sm(z,1.375,1.435))
 elif part in (8,10):
  w=mix({f'B_{s}_Foot':1},{f'B_{s}_Calf':1},sm(z,.075,.15))
  w=mix(w,{f'B_{s}_Thigh':1},sm(z,.475,.575))
 else:continue
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for n,wgt in w.items():
  if wgt>1e-6:o.vertex_groups[n].add([v.index],wgt,'REPLACE')
me.attributes['orig_co'].data.foreach_set('vector',np.array([v.co[:] for v in me.vertices]).ravel())
# Body contact, not only boot soles, determines fall height for this fitted skeleton.
sc=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
pv=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices])
solid=(pv!=100)|(co[:,2]>1.02);sample=[];need=[]
for f in np.arange(0,float(a.frame_range[1])+.01,.25):
 sc.frame_set(int(f),subframe=float(f%1))
 loc=r.pose.bones['B_Pelvis'].location.copy()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh()
 floor=min(v.co.z for v in mm.vertices if solid[v.index]);ev.to_mesh_clear()
 sample.append((float(f),loc));need.append(max(0,.003-floor))
need=np.array(need);kernel=np.exp(-.5*(np.arange(-8,9)/4)**2);kernel/=kernel.sum()
padded=np.pad(need,8,mode='edge');soft=np.convolve(padded,kernel,mode='valid');lift=np.maximum(need,soft)
for (f,loc),dz in zip(sample,lift):
 sc.frame_set(int(f),subframe=f%1)
 pel=r.pose.bones['B_Pelvis'];parent=pel.parent
 basis=parent.matrix@parent.bone.matrix_local.inverted()@pel.bone.matrix_local if parent else pel.bone.matrix_local
 delta=basis.to_3x3().inverted()@Vector((0,0,float(dz)))
 b=r.pose.bones['B_Pelvis'];b.location=loc+delta;b.keyframe_insert('location',frame=f)
for l in a.layers:
 for strip in l.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if fc.data_path.endswith('location'):
     for k in fc.keyframe_points:k.interpolation='LINEAR'
print('FALL body ground lift max cm',float(lift.max()*100))
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/body_complete.blend'))
print('COMPLETED LEGS',len(me.vertices),sum(len(f.vertices)-2 for f in me.polygons))
