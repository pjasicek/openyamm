"""Retain the single-eye face and teeth; remove malformed eyebrow specks and fit native hair volume."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys,math
from mathutils.bvhtree import BVHTree
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_parts.blend'))
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name not in ['H00','H01','H02']:bpy.data.objects.remove(o,do_unlink=True)
report={'removed_eyebrow_components':109,'parts':[]}
for o in [bpy.data.objects[n] for n in ['H00','H01','H02']]:
 bm=bmesh.new();bm.from_mesh(o.data);todo=set(bm.faces);parts=[]
 while todo:
  f=todo.pop();stack=[f];component=[f]
  while stack:
   f=stack.pop()
   for e in f.edges:
    for n in e.link_faces:
     if n in todo:todo.remove(n);stack.append(n);component.append(n)
  parts.append(component)
 parts.sort(key=len,reverse=True);discard=[f for c in parts[1:] for f in c]
 if discard:bmesh.ops.delete(bm,geom=discard,context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bad=[e for e in bm.edges if not e.is_manifold and not e.is_boundary]
 if bad:
  assert o.name=='H00' and len(bad)==1
  vertices={v for e in bad for v in e.verts};assert all(.08<v.co.x<.11 and .17<v.co.z<.2 for v in vertices)
  bmesh.ops.delete(bm,geom=list(vertices),context='VERTS')
 edges=[e for e in bm.edges if e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=20)
 remaining=[e for e in bm.edges if e.is_boundary]
 if remaining:
  verts={v for e in remaining for v in e.verts}
  assert o.name=='H00' and len(remaining)==5
  print('REMAINING_BOUNDARY',[(list(v.co),sum(e.is_boundary for e in v.link_edges)) for v in verts],flush=True)
  assert all(sum(e.is_boundary for e in v.link_edges)==2 for v in verts)
  centre=bm.verts.new(sum((v.co for v in verts),Vector())/len(verts))
  for e in remaining:bm.faces.new([e.verts[0],e.verts[1],centre])
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 row={'part':o.name,'discarded_edge_components':len(parts)-1,'discarded_faces':len(discard),'capped_root_edges':len(edges),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
 print('HEAD_CLEAN_PART',row,flush=True);report['parts'].append(row)
 assert row['boundary']==row['nonmanifold']==0
 bm.to_mesh(o.data);bm.free()
for o in bpy.data.objects:o.select_set(o.type=='MESH')
head=bpy.data.objects['H00'];bpy.context.view_layer.objects.active=head;bpy.ops.object.join();head.name='HeadSource'
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0);scale=.53/(hi[2]-lo[2])
head.scale=(scale,)*3;head.location=(-float((lo[0]+hi[0])/2)*scale,-float((lo[1]+hi[1])/2)*scale,2.4-float(hi[2])*scale);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
with bpy.data.libraries.load(str(p/'work/head_reduced_30.blend'),link=False) as (src,dst):dst.objects=['HeadSource']
hair=dst.objects[0];co=np.array([tuple(v.co) for v in hair.data.vertices]);lo=co.min(0);hi=co.max(0);scale=.53/(hi[2]-lo[2]);offset=Vector((-float((lo[0]+hi[0])/2)*scale,-float((lo[1]+hi[1])/2)*scale,2.4-float(hi[2])*scale))
bm=bmesh.new();bm.from_mesh(hair.data)
for v in bm.verts:v.co=v.co*scale+offset
tree=BVHTree.FromBMesh(bm);bm.free();bpy.data.objects.remove(hair,do_unlink=True)
def hair_weight(v):
 x,y,z=v.co
 back=float(np.clip((y-.015)/.05,0,1)*np.clip((2.33-z)/.06,0,1))
 side=float(np.clip((abs(x)-.135)/.04,0,1)*np.clip((2.15-z)/.035,0,1))
 weight=max(back,side)
 if 2.13<z<2.28 and abs(x)>.13 and y<.04:weight=0
 return weight
bm=bmesh.new();bm.from_mesh(head.data)
faces=[f for f in bm.faces if all(hair_weight(v)>.15 for v in f.verts)];edges={e for f in faces for e in f.edges}
bmesh.ops.subdivide_edges(bm,edges=list(edges),cuts=2,use_grid_fill=True)
count=0;hairverts=[]
for v in bm.verts:
 weight=hair_weight(v)
 if weight>0:
  point=tree.find_nearest(v.co)[0];distance=(point-v.co).length
  v.co=v.co.lerp(point,weight*min(1,.03/max(distance,1e-8)));count+=1;hairverts.append(v)
for _ in range(4):bmesh.ops.smooth_vert(bm,verts=hairverts,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
# Replace the tiny generated crown pit with one clean rounded cap.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,2.375),plane_no=(0,0,1),clear_outer=True)
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
ring=[v for v in bm.verts if abs(v.co.z-2.375)<1e-5 and any(e.is_boundary for e in v.link_edges)]
assert len(ring)>8 and all(sum(e.is_boundary for e in v.link_edges)==2 for v in ring)
centre=sum((v.co for v in ring),Vector())/len(ring);ring.sort(key=lambda v:math.atan2(v.co.y-centre.y,v.co.x-centre.x))
assert all(any(e.other_vert(v)==ring[(i+1)%len(ring)] for e in v.link_edges) for i,v in enumerate(ring))
inner=[bm.verts.new((v.co.x*.5+centre.x*.5,v.co.y*.5+centre.y*.5,2.395)) for v in ring];tip=bm.verts.new((centre.x,centre.y,2.4))
for i,v in enumerate(ring):
 j=(i+1)%len(ring);bm.faces.new([v,ring[j],inner[j],inner[i]]);bm.faces.new([inner[i],inner[j],tip])
bm.to_mesh(head.data);bm.free()
bpy.context.view_layer.objects.active=head;head.select_set(True)
group=head.vertex_groups.new(name='HairReduction')
for v in head.data.vertices:group.add([v.index],1 if hair_weight(v)>.1 else 0,'REPLACE')
mod=head.modifiers.new('Hair silhouette budget','DECIMATE');mod.ratio=11000/sum(len(f.vertices)-2 for f in head.data.polygons);mod.vertex_group=group.name;mod.vertex_group_factor=.1;bpy.ops.object.modifier_apply(modifier=mod.name);head.vertex_groups.clear()
head.data.materials.clear();mat=bpy.data.materials.new('HeadClay');mat.diffuse_color=(.65,.53,.43,1);head.data.materials.append(mat)
for f in head.data.polygons:f.material_index=0;f.use_smooth=True
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
report['hair_volume_vertices']=count;report['triangles']=sum(len(f.vertices)-2 for f in head.data.polygons)
(p/'work/head_selected.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_selected.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_selected'),2.135,.62,views=('front','left','back','three_quarter'),resolution=(650,650))
