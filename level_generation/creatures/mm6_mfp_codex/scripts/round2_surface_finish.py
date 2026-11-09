"""Project lower-LOD faces onto matching source pieces and one continuous UV island; refresh smooth skin normals after the old hole repair."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2';base=np.load(W/'mesh0.npz');ids=np.flatnonzero(base['mat']==0);report={}
# Group source triangles by continuous old AND new parameter coordinates. Lower-LOD
# faces must stay on one packed island even when a corner is close to another seam.
parents=list(range(len(ids)));edges={}
def root(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
for i,fi in enumerate(ids):
 vs=base['tri'][fi];old=base['old_uv'][fi];new=base['uv'][fi]
 for j in range(3):
  k=(j+1)%3;e=tuple(sorted([(int(vs[j]),*np.round(old[j],6),*np.round(new[j],6)),(int(vs[k]),*np.round(old[k],6),*np.round(new[k],6))]))
  if e in edges:parents[root(i)]=root(edges[e])
  else:edges[e]=i
from collections import defaultdict
groups=defaultdict(list)
for i,fi in enumerate(ids):groups[root(i)].append(fi)
def surface_tree(faces):
 triangles=base['co'][base['tri'][faces]]
 return BVHTree.FromPolygons([Vector(v)for row in triangles for v in row],[(3*i,3*i+1,3*i+2)for i in range(len(faces))])
island_trees={key:surface_tree(faces)for key,faces in groups.items()}
piece_faces=defaultdict(list)
for i,fi in enumerate(ids):
 vals,count=np.unique(base['piece'][base['tri'][fi]],return_counts=True);piece_faces[int(vals[count.argmax()])].append(fi)
piece_trees={key:surface_tree(faces)for key,faces in piece_faces.items()};source_island={fi:root(i)for i,fi in enumerate(ids)}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(W/f'lod{level}.blend'));b=bpy.data.objects['Body'];m=b.data;m.calc_loop_triangles();data=dict(np.load(W/f'mesh{level}.npz'));uv=m.uv_layers['UVMap'].data;cache={}
 if level:
  pv=[v.value for v in m.attributes['piece'].data]
  for face in m.polygons:
   if face.material_index!=0:continue
   vals,count=np.unique([pv[i]for i in face.vertices],return_counts=True);piece=int(vals[count.argmax()])
   candidates=piece_faces.get(piece,ids);candidate_tree=piece_trees.get(piece)
   if candidate_tree is None:candidate_tree=surface_tree(candidates)
   center=sum((m.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
   _,_,si,_=candidate_tree.find_nearest(center);island=source_island[candidates[si]]
   local_tree=island_trees[island];source_ids=groups[island]
   for li in face.loop_indices:
    q=m.vertices[m.loops[li].vertex_index].co;key=(island,*tuple(round(v,7)for v in q))
    if key not in cache:
     near,_,si,_=local_tree.find_nearest(q);fi=source_ids[si];A=base['co'][base['tri'][fi]];C=base['uv'][fi]
     w=np.linalg.pinv(np.column_stack((A[1]-A[0],A[2]-A[0])))@(np.array(near)-A[0]);cache[key]=C[0]+w[0]*(C[1]-C[0])+w[1]*(C[2]-C[0])
    uv[li].uv=cache[key]
 # Area-weighted normals across coincident skin seam vertices; preserve existing accessory normals.
 pv=[v.value for v in m.attributes['piece'].data];total={}
 for f in m.polygons:
  for vi in f.vertices:
   if pv[vi] in [0,4,5]:
    key=(pv[vi],*tuple(round(v,6)for v in m.vertices[vi].co));total[key]=total.get(key,Vector())+f.normal*f.area
 normals=[]
 for loop,normal in zip(m.loops,m.corner_normals):
  vi=loop.vertex_index;key=(pv[vi],*tuple(round(v,6)for v in m.vertices[vi].co));normals.append(total[key].normalized()if key in total and total[key].length>1e-9 else normal.vector.copy())
 m.normals_split_custom_set(normals);m.update();data['uv']=np.array([[uv[i].uv[:]for i in t.loops]for t in m.loop_triangles]);np.savez_compressed(W/f'mesh{level}.npz',**data)
 report[str(level)]={'unchanged_triangles':len(m.loop_triangles),'continuous_uv_vertices':len(cache),'smooth_skin_vertices':len(total)};bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}.blend'))
(P/'review/round2/surface_finish.json').write_text(json.dumps(report,indent=2))
