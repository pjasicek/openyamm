from pathlib import Path
import sys,json,math,bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));import common
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/imported.blend'))
ob=bpy.data.objects['Body'];old=ob.data
labels=np.array([x.value for x in old.attributes['piece'].data])
# Keep the untouched upper body and the original exposed lower legs. Only rebuild the hidden hip transition.
bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if labels[v.index]!=1],context='VERTS')
tree=BVHTree.FromBMesh(bm)
# Outer wrap follows the original radial envelope; its free hem is independent of the leg skin.
verts=[];faces=[];n=80;rows=15;bad=0
for j in range(rows):
 t=j/(rows-1)
 for i in range(n):
  a=2*math.pi*i/n;dx,dy=math.sin(a),-math.cos(a)
  # Preserve the central pointed front/back and raised diagonal hem.
  hem=.728+.050*abs(math.sin(2*a))
  z=1.245*(1-t)+hem*t
  hit,normal,idx,dist=tree.ray_cast(Vector((dx,.035+dy,z)),Vector((-dx,-dy,0)),1.0)
  if hit is None:
   bad+=1;rx=.18*(1-t)+.315*t;ry=.135*(1-t)+.18*t;rad=1/math.sqrt((dx/rx)**2+(dy/ry)**2);hit=Vector((dx*rad,.035+dy*rad,z))
  # A ray near the hem can reach the thigh after the cloth ends: continue the cloth's preceding radius.
  if j>0:
   prev=Vector(verts[(j-1)*n+i]);r0=math.hypot(prev.x,prev.y-.035);r=math.hypot(hit.x,hit.y-.035)
   if r<r0*.87:hit=Vector((dx*r0,.035+dy*r0,z))
  verts.append(tuple(hit))
for j in range(rows-1):
 for i in range(n):
  a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+(i+1)%n;d=(j+1)*n+i;faces.append((a,b,c,d))
wrap=bpy.data.meshes.new('Wrap');wrap.from_pydata(verts,[],faces);wrap.update()
bm.free()
# Leg cuts are hidden inside the wrap; the original knee/calf/hoof topology is retained.
bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if labels[v.index]!=1],context='VERTS')
bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,.68),plane_no=(0,0,1),clear_outer=True)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# Remove the detached central cloth-tip remnant beneath the cutting plane.
seen=set();discard=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];part=[]
 while stack:
  q=stack.pop()
  if q in seen:continue
  seen.add(q);part.append(q);stack.extend(e.other_vert(q) for e in q.link_edges)
 if min(q.co.z for q in part)>.1:discard.extend(part)
bmesh.ops.delete(bm,geom=discard,context='VERTS')
# Ordered cut rings.
def boundary_loops(mesh):
 edges={e for e in mesh.edges if e.is_boundary};out=[]
 while edges:
  e=next(iter(edges));start=e.verts[0];cur=e.verts[1];seq=[start,cur];edges.remove(e)
  while cur is not start:
   nxt=next((q for q in cur.link_edges if q in edges),None)
   if nxt is None:break
   edges.remove(nxt);cur=nxt.other_vert(cur)
   if cur is not start:seq.append(cur)
  assert cur is start
  out.append(seq)
 return out
rings=boundary_loops(bm);print('CUT RINGS',[(len(r),list(sum((v.co for v in r),Vector())/len(r))) for r in rings]);assert len(rings)==2 and all(min(v.co.z for v in r)>.679 for r in rings)
for ring in rings:
 c=sum((v.co for v in ring),Vector())/len(ring);sg=1 if c.x>0 else -1
 previous=ring
 for z,xc,rx,ry,yc in [(.75,.160,.095,.100,.050),(.81,.155,.100,.110,.045),(.90,.140,.105,.120,.035),(1.00,.120,.110,.125,.035),(1.11,.115,.100,.120,.03)]:
  new=[]
  for v in ring:
   angle=math.atan2((v.co.y-c.y)/.10,(v.co.x-c.x)/.10)
   new.append(bm.verts.new((sg*xc+rx*math.cos(angle),yc+ry*math.sin(angle),z)))
  for i in range(len(ring)):bm.faces.new((previous[i],previous[(i+1)%len(ring)],new[(i+1)%len(ring)],new[i]))
  previous=new
 # Temporary cap becomes internal after boolean union with the pelvis.
 bm.faces.new(previous)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);legme=bpy.data.meshes.new('LegSkin');bm.to_mesh(legme);bm.free()
legs=bpy.data.objects.new('LegSkin',legme);bpy.context.collection.objects.link(legs)
# Elliptical pelvis, connected to both upper thighs by an exact union, then joined to the native waist ring.
bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=(0,.027,1.09));pelvis=bpy.context.object
pelvis.scale=(.205,.135,.16);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
mod=legs.modifiers.new('Hidden pelvis union','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=pelvis
bpy.context.view_layer.objects.active=legs;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(pelvis,do_unlink=True)
# Keep the upper body and cuffs, discard two stray triangles. Close confirmed small skin tears locally.
bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if labels[v.index] not in (0,2,3,4)],context='VERTS')
for ring in boundary_loops(bm):
 if len(ring)<=5:bm.faces.new(ring)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(old);bm.free()
# The native torso is open beneath its belt. Close against the hidden pelvis via a short waist bridge.
# A boolean union would include overlapping cuffs; only union the body skin component.
bpy.context.view_layer.objects.active=ob
for o in bpy.context.scene.objects:o.select_set(o is ob)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and o is not legs]
skin=max(parts,key=lambda o:len(o.data.vertices))
bm=bmesh.new();bm.from_mesh(legs.data)
assert all(e.is_manifold for e in bm.edges)
bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,1.185),plane_no=(0,0,1),clear_outer=True)
bm.to_mesh(legs.data);bm.free()
for o in bpy.context.scene.objects:o.select_set(o in (skin,legs))
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(skin.data)
loops=boundary_loops(bm);assert len(loops)==2
# Monotone angular zipper preserves both original boundary rings without resampling exposed skin.
rings=[]
for ring in loops:
 c=sum((v.co for v in ring),Vector())/len(ring)
 seq=sorted([(math.atan2(v.co.y-c.y,v.co.x-c.x)%(2*math.pi),v) for v in ring],key=lambda x:x[0])
 rings.append(seq)
a,b=rings;i=j=0
while i<len(a) or j<len(b):
 na=a[(i+1)%len(a)][0]+(2*math.pi if i+1>=len(a) else 0) if i<len(a) else 99
 nb=b[(j+1)%len(b)][0]+(2*math.pi if j+1>=len(b) else 0) if j<len(b) else 99
 if na<nb:
  bm.faces.new((a[i%len(a)][1],a[(i+1)%len(a)][1],b[j%len(b)][1]));i+=1
 else:
  bm.faces.new((a[i%len(a)][1],b[(j+1)%len(b)][1],b[j%len(b)][1]));j+=1
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(skin.data);bm.free()
# The hidden body is fitted inside the measured garment, with a smooth return to the native waist.
for v in skin.data.vertices:
 z=v.co.z
 if .73<z<1.225 and abs(v.co.x)<.35:
  t=min(1.,(z-.73)/.16,(1.225-z)/.06);t=t*t*(3-2*t)
  v.co.x*=1-.16*t;v.co.y=.027+(v.co.y-.027)*(1-.42*t)
# Stable semantic labels survive rigging and texture transfer.
wrapob=bpy.data.objects.new('Wrap',wrap);bpy.context.collection.objects.link(wrapob)
parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in parts:
 if o is skin:label=0
 elif o is wrapob:label=1
 else:
  co=np.array([v.co[:] for v in o.data.vertices]);label=2 if abs(co[:,0].mean())<.25 else (3 if co[:,0].mean()>0 else 4)
 if 'piece' in o.data.attributes:o.data.attributes.remove(o.data.attributes['piece'])
 attr=o.data.attributes.new('piece','INT','POINT');attr.data.foreach_set('value',np.full(len(o.data.vertices),label,dtype=np.int32))
 o.data.materials.clear()
 mat=bpy.data.materials.new('Provisional_'+str(label));mat.use_nodes=True
 col=(.55,.55,.55,1) if label==0 else ((.12,.25,.09,1) if label==1 else (.45,.3,.12,1))
 mat.diffuse_color=col;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=.8
 im=bpy.data.images.new('provisional_'+str(label),16,16);im.generated_color=col;im.pack()
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0;f.use_smooth=True
 for obj in bpy.context.scene.objects:obj.select_set(obj is o)
 bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();body=bpy.context.object;body.name='Body'
me=body.data
if 'orig_co' in me.attributes:me.attributes.remove(me.attributes['orig_co'])
me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',np.array([v.co[:] for v in me.vertices]).ravel())
# Trust boundary: the body skin must be closed, and all exported vertices finite.
lab=np.array([x.value for x in me.attributes['piece'].data]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if lab[v.index]!=0],context='VERTS')
assert all(e.is_manifold for e in bm.edges),[(e.index,len(e.link_faces),[list(v.co) for v in e.verts]) for e in bm.edges if not e.is_manifold][:20]
assert all(math.isfinite(a) for v in me.vertices for a in v.co)
report={'skin_closed':True,'skin_vertices':len(bm.verts),'total_triangles':sum(len(f.vertices)-2 for f in me.polygons),'wrap_rays_without_hit':bad,'repairs':['four small skin tears filled','two loose triangles discarded','garment separated from legs','closed hidden pelvis and thigh skin joined to original torso','wrap radial envelope rebuilt from original surface; free hem']};bm.free()
(p/'review/geometry/repair.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/rig_upload.glb'),export_format='GLB',use_selection=True,export_animations=False)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/geometry/repaired'),1.05,2.35,views=('front','left','back','three_quarter'),resolution=(960,960))
