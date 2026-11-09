"""Repair the confirmed boot hole and restore the three round native necklace discs."""
from pathlib import Path
import bpy,bmesh,sys,math,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v2_parts.blend'))
for o in list(bpy.data.objects):
 if o.type=='MESH' and int(o.name[1:])>=9:bpy.data.objects.remove(o,do_unlink=True)
leg=bpy.data.objects['P01'];bm=bmesh.new();bm.from_mesh(leg.data)
hole=[e for e in bm.edges if e.is_boundary and all(v.co.z<.3 for v in e.verts)]
assert len(hole)==4,len(hole)
bmesh.ops.holes_fill(bm,edges=hole,sides=4)
left=[e for e in bm.edges if e.is_boundary and all(v.co.z<.3 for v in e.verts)]
if left:
 verts={v for e in left for v in e.verts};assert len(left)==4 and all(sum(e.is_boundary for e in v.link_edges)==2 for v in verts)
 centre=bm.verts.new(sum((v.co for v in verts),Vector())/len(verts))
 for e in left:bm.faces.new([e.verts[0],e.verts[1],centre])
assert not any(e.is_boundary and any(v.co.z<.3 for v in e.verts) for e in bm.edges)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(leg.data);bm.free()
discs=[]
skin=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(skin.data);tree=BVHTree.FromBMesh(bm);bm.free()
for name in ['P06','P07','P08']:
 o=bpy.data.objects[name];co=[v.co.copy() for v in o.data.vertices]
 lo=Vector(tuple(min(v[i] for v in co) for i in range(3)));hi=Vector(tuple(max(v[i] for v in co) for i in range(3)))
 centre=(lo+hi)/2;radius=(hi.x-lo.x)/2;centre.z=hi.z-radius
 ys=[]
 for a in range(24):
  x=centre.x+radius*math.cos(a*math.tau/24);z=centre.z+radius*math.sin(a*math.tau/24)
  hit=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))[0]
  if hit is not None:ys.append(hit.y)
 dy=min(ys)-.012-centre.y;centre.y+=dy
 loop=min([bpy.data.objects[n] for n in ['P03','P04','P05']],key=lambda q:abs(sum(v.co.x for v in q.data.vertices)/len(q.data.vertices)-centre.x))
 zmin=min(v.co.z for v in loop.data.vertices);zmax=max(v.co.z for v in loop.data.vertices)
 for v in loop.data.vertices:v.co.y+=dy*(zmax-v.co.z)/(zmax-zmin)
 mat=o.data.materials[0];bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=.009,location=centre,rotation=(math.pi/2,0,0))
 o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 bevel=o.modifiers.new('Disc rounded rim','BEVEL');bevel.width=.002;bevel.segments=1;bpy.ops.object.modifier_apply(modifier=bevel.name)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 discs.append({'part':name,'centre':list(centre),'radius':radius})
for o in bpy.data.objects:
 if o.type=='MESH':
  layer=o.data.attributes.new('piece','INT','POINT');layer.data.foreach_set('value',[int(o.name[1:])]*len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/body_clean.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/body_clean'),1.2,3.1,views=('front','back'),resolution=(600,900))
(p/'work/body_cleanup.json').write_text(json.dumps({'closed_boot_boundary_edges':4,'discarded_stray_parts':list(range(9,16)),'round_discs':discs},indent=2))
