"""Restore damaged cleanup vertices and replace the overlapping neck with a connected loft."""
import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_neck_master.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];bm=bmesh.new();bm.from_mesh(o.data);deform=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv.active
# Meshy supplied a fan of disconnected sliver tips at this one point. Remove the tips,
# then weld coincident UV seam vertices (loop UVs remain independent).
spikes=[v for v in bm.verts if (v.co-Vector((.01595552,-.342351,.316081))).length<1e-5]
restored=[{'removed_sliver_tip':v.co[:]} for v in spikes]
assert len(spikes)==21
bmesh.ops.delete(bm,geom=spikes,context='VERTS')
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if any(f.material_index in [0,1] for f in v.link_faces)],dist=.0003)
# Small triangular fins along the forearms are also failed topology, not native spines.
spikes=[f for f in bm.faces if f.material_index==0 and f.calc_center_median().y<-.35 and f.calc_center_median().z<.25 and max(e.calc_length() for e in f.edges)>.055 and f.calc_area()/max(e.calc_length() for e in f.edges)**2<.09]
print('REMOVED',len(restored),'tips',len(spikes),'forearm fins',flush=True)
bmesh.ops.delete(bm,geom=spikes,context='FACES')
# Cut the old body neck on an undamaged, simple section.
bodyfaces=[f for f in bm.faces if f.material_index==0 and all(abs(v.co.x)<.15 and v.co.y<-.15 for v in f.verts)]
geom=list({v for f in bodyfaces for v in f.verts}|{e for f in bodyfaces for e in f.edges}|set(bodyfaces))
bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=(0,0,.525),plane_no=(0,0,1))
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==0 and f.calc_center_median().z>.525 and abs(f.calc_center_median().x)<.15 and f.calc_center_median().y<-.15],context='FACES')
# Keep the skull, jaws and fins. Only the extra lower neck stub is removed.
headfaces=[f for f in bm.faces if f.material_index==1]
geom=list({v for f in headfaces for v in f.verts}|{e for f in headfaces for e in f.edges}|set(headfaces))
bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=(0,0,.59),plane_no=(0,0,1))
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==1 and f.calc_center_median().z<.59],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# Closed rings at both cut planes; cap only separate fin stumps, not the mouth.
def cutloops(z,slot):
 es={e for e in bm.edges if e.is_boundary and all(abs(v.co.z-z)<2e-5 for v in e.verts) and any(f.material_index==slot for f in e.link_faces)};out=[]
 while es:
  start=es.pop();component={start};stack=[start]
  while stack:
   e=stack.pop()
   for v in e.verts:
    for q in v.link_edges:
     if q in es:es.remove(q);component.add(q);stack.append(q)
  out.append(component)
 return sorted(out,key=lambda es:-sum(e.calc_length() for e in es))
lower=cutloops(.525,0);upper=cutloops(.59,1);print('RINGS',[(len(e),sum(q.calc_length() for q in e)) for e in lower],[(len(e),sum(q.calc_length() for q in e)) for e in upper],flush=True)
assert lower and upper
A={v for e in lower[0] for v in e.verts};B={v for e in upper[0] for v in e.verts}
print('RING_VERTICES',len(A),len(B),flush=True);assert len(A)==len(lower[0]) and len(B) in [len(upper[0]),len(upper[0])+1]
for group in lower[1:]+upper[1:]:bmesh.ops.holes_fill(bm,edges=list(group),sides=0)
# Angular zipper and interpolated cross-sections follow the shared Hydra graft pattern.
cA=sum((v.co for v in A),Vector())/len(A);cB=sum((v.co for v in B),Vector())/len(B)
def ordered(vs,c):return sorted(vs,key=lambda v:math.atan2(v.co.y-c.y,v.co.x-c.x))
A=ordered(A,cA);B=ordered(B,cB)
def profile(vs,c,angle):
 aa=np.array([math.atan2(v.co.y-c.y,v.co.x-c.x) for v in vs]);rr=np.array([(v.co-c).xy.length for v in vs]);return np.interp(angle,aa,rr,period=2*math.pi)
newfaces=[];rings=[A];n=48
for k in range(1,5):
 t=k/5;c=cA.lerp(cB,t);ring=[]
 for j in range(n):
  a=-math.pi+2*math.pi*j/n;r=(1-t)*profile(A,cA,a)+t*profile(B,cB,a);v=bm.verts.new(c+Vector((r*math.cos(a),r*math.sin(a),0)));v[deform][o.vertex_groups['Neck3'].index]=1-t;v[deform][o.vertex_groups['Head'].index]=t;ring.append(v)
 rings.append(ring)
rings.append(B)
for v in A:v[deform].clear();v[deform][o.vertex_groups['Neck3'].index]=1.
for v in B:v[deform].clear();v[deform][o.vertex_groups['Head'].index]=1.
for aa,bb in zip(rings[:-1],rings[1:]):
 i=j=0
 while i<len(aa) or j<len(bb):
  if j==len(bb) or (i<len(aa) and (i+1)/len(aa)<=(j+1)/len(bb)):
   vs=(aa[i%len(aa)],aa[(i+1)%len(aa)],bb[j%len(bb)]);i+=1
  else:vs=(aa[i%len(aa)],bb[(j+1)%len(bb)],bb[j%len(bb)]);j+=1
  f=bm.faces.new(vs);f.material_index=0;f.smooth=True;newfaces.append(f)
# Close local accidental holes on skin; preserve the mouth and outer membrane boundaries.
left={e for e in bm.edges if e.is_boundary};patched=0
while left:
 e=left.pop();es={e};stack=[e]
 while stack:
  q=stack.pop()
  for v in q.verts:
   for nedge in v.link_edges:
    if nedge in left:left.remove(nedge);es.add(nedge);stack.append(nedge)
 vs={v for e in es for v in e.verts};slots={f.material_index for e in es for f in e.link_faces}
 if slots <= {0,2} and max(np.ptp(np.array([v.co[:] for v in vs]),axis=0))<.12 and len(es)==len(vs):
  fs=bmesh.ops.holes_fill(bm,edges=list(es),sides=0)['faces'];patched+=len(fs)
  for f in fs:f.material_index=min(slots);f.smooth=True
es=[e for e in bm.edges if e.is_boundary and all(f.material_index==0 for f in e.link_faces)]
fs=bmesh.ops.holes_fill(bm,edges=es,sides=32)['faces']
for f in fs:f.material_index=0;f.smooth=True
print('BODY_CAPS',len(fs),flush=True)
# Several source holes meet at a vertex: fill their shortest individual cycles.
from collections import deque
cyclecaps=0
for _ in range(3):
 boundary=[e for e in bm.edges if e.is_boundary and all(f.material_index==0 for f in e.link_faces)]
 for edge in boundary:
  if not edge.is_boundary:continue
  start,end=edge.verts;queue=deque([(start,[start])]);visited={start};path=None
  while queue:
   v,route=queue.popleft()
   if len(route)>24:continue
   for e in v.link_edges:
    if e==edge or not e.is_boundary or not all(f.material_index==0 for f in e.link_faces):continue
    w=e.other_vert(v)
    if w==end:path=route+[w];break
    if w not in visited:visited.add(w);queue.append((w,route+[w]))
   if path:break
  if path and len(path)>=3 and max(np.ptp(np.array([v.co[:] for v in path]),axis=0))<.15:
   try:f=bm.faces.new(path)
   except ValueError:continue
   f.material_index=0;f.smooth=True;cyclecaps+=1
print('CYCLE_CAPS',cyclecaps,flush=True)
# Relax the loft's two join bands without changing the skull or chest silhouette.
neckverts={v for f in newfaces for v in f.verts}
for _ in range(4):
 positions={v:v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),.28) for v in neckverts}
 for v,c in positions.items():v.co=c
print('PATCHED_HOLES',patched,flush=True)
for f in bm.faces:
 if f.material_index==1 and f.calc_center_median().z<.66 and f.calc_center_median().y>-.40:f.material_index=0
# Body will receive a new coherent retexture, including the actual connected neck.
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
assert all(not e.is_boundary for e in lower[0]|upper[0])
bm.to_mesh(o.data);bm.free();o.data.update();o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in o.data.polygons:f.select=f.material_index==0
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003);bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/repaired_geometry.blend'));(P/'work/repair_geometry.json').write_text(json.dumps({'restored':restored,'loft_faces':len(newfaces),'cut_rings':[len(A),len(B)]},indent=2))
