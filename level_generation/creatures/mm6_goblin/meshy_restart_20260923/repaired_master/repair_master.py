"""Localized geometry repair of archived master 01; preserve both original candidates."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/repaired_master')
old=bpy.data.scenes.get('MM6 Goblin Restart - Repaired Master')
if old:old.name='MM6 Goblin Repair Draft'
s=bpy.data.scenes.new('MM6 Goblin Restart - Repaired Master');bpy.context.window.scene=s
bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'master_01/source.glb'))
body=next(o for o in s.objects if o.type=='MESH');body.name='Goblin Source Body - Local Repairs'
def smooth(v):
 v=max(0,min(1,v));return v*v*(3-2*v)
changed_head=changed_teeth=0
for v in body.data.vertices:
 x,y,z=v.co
 # Body geometry is in Blender world axes after glTF import (identity object transform verified below).
 if .70<z<.95 and y>.015 and abs(x)<.14:
  wx=math.exp(-(x/.085)**2)*(1-smooth((abs(x)-.09)/.05))
  wz=math.exp(-abs((z-.835)/.064)**1.6)*smooth((z-.70)/.04)*(1-smooth((z-.925)/.025))
  shift=.070*wx*wz*smooth((y-.015)/.09)
  if shift>1e-7:v.co.y+=shift;changed_head+=1
 if .724<z<.759 and abs(x)<.065 and y<-.130:
  w=smooth((z-.724)/.007)*(1-smooth((z-.754)/.005))
  v.co.y=y+(-.130-y)*.78*w;changed_teeth+=1
# Keep the original ear intact. Its small unwanted jewelry is deferred to the editable remesh;
# cutting a fused million-triangle ear damaged its surface in the rejected local experiment.
removed=patch_count=0
bm=bmesh.new();bm.from_mesh(body.data);remaining_boundaries=sum(e.is_boundary for e in bm.edges);bm.free()
body.data.update()
# Sample the actual upper-back surface; plates follow its curvature and remain separate editable armor objects.
points=[v.co.copy() for v in body.data.vertices if abs(v.co.x)<.23 and .39<v.co.z<.68 and v.co.y>.105]
kdt=KDTree(len(points))
for i,p in enumerate(points):kdt.insert(Vector((p.x,p.z,0)),i)
kdt.balance()
def surface(x,z):
 near=kdt.find_n(Vector((x,z,0)),8)
 return max(points[i].y for co,i,dist in near)
mat=body.data.materials[0]
outline=[(.018,.587),(.056,.613),(.147,.600),(.174,.528),(.148,.464),(.037,.474)]
parts=[]
for side in [-1,1]:
 coords=[(side*x,z) for x,z in outline];cx=sum(x for x,z in coords)/len(coords);cz=sum(z for x,z in coords)/len(coords)
 verts=[];faces=[]
 # Three perimeter rings: buried rear rim, visible rim, then bevel inset.
 for scale,offset in [(1,.001),(1,.009),(.94,.013)]:
  for x,z in coords:
   xx=cx+(x-cx)*scale;zz=cz+(z-cz)*scale;verts.append((xx,surface(xx,zz)+offset,zz))
 count=len(coords);verts.append((cx,surface(cx,cz)+.017,cz));center=len(verts)-1
 for ring in range(2):
  for j in range(count):n=(j+1)%count;faces.append((ring*count+j,ring*count+n,(ring+1)*count+n,(ring+1)*count+j))
 for j in range(count):faces.append((count*2+j,count*2+(j+1)%count,center))
 faces.append(tuple(reversed(range(count))))
 mesh=bpy.data.meshes.new('Curved upper-back plate');mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update()
 for polygon in mesh.polygons:polygon.use_smooth=True
 o=bpy.data.objects.new('Upper-back plate '+('R' if side<0 else 'L'),mesh);s.collection.objects.link(o);parts.append(o.name)
 bb=bmesh.new();bb.from_mesh(mesh);bmesh.ops.recalc_face_normals(bb,faces=list(bb.faces));bb.to_mesh(mesh);bb.free()
 for j,(x,z) in enumerate(coords):
  xx=cx+(x-cx)*.81;zz=cz+(z-cz)*.81
  bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.0036,location=(xx,surface(xx,zz)+.014,zz))
  rivet=bpy.context.object;rivet.name='Back plate rivet';rivet.scale=(1,.5,1);rivet.data.materials.append(mat)
  for p in rivet.data.polygons:p.use_smooth=True
report={'source':'../master_01/source.glb','scene':s.name,'body':body.name,'skull_vertices_adjusted':changed_head,'tooth_vertices_adjusted':changed_teeth,'left_ear_region_vertices_removed':removed,'patch_faces':patch_count,'remaining_boundary_edges':remaining_boundaries,'added_armor_objects':parts,'object_matrix':list(map(list,body.matrix_world))}
(ROOT/'repair_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
