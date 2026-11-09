"""Join the three cut body loops with a weighted, fur-mapped pelvis; preserve every old vertex and action."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
# The unreduced, pre-deletion skin supplies the anatomical cross section.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6.blend'))
src=bpy.data.objects['Body'];pv=src.data.attributes['piece'].data
surface=BVHTree.FromPolygons([v.co[:] for v in src.data.vertices],[tuple(f.vertices) for f in src.data.polygons if all(pv[i].value==0 for i in f.vertices)])
def components(edges):
 remaining=set(edges);result=[]
 while remaining:
  e=remaining.pop();es={e};todo=list(e.verts)
  while todo:
   v=todo.pop()
   for q in v.link_edges:
    if q in remaining:remaining.remove(q);es.add(q);todo.extend(q.verts)
  result.append(es)
 return result
def ordered(es):
 e=min(es,key=lambda e: min(v.index for v in e.verts));start=e.verts[0];out=[start];v=e.other_vert(start)
 while v!=start:
  out.append(v);n=[q for q in v.link_edges if q in es and q!=e];assert len(n)==1
  e=n[0];v=e.other_vert(v)
 assert len(out)==len(es)
 return out
def ccw(loop):
 area=sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(loop,loop[1:]+loop[:1]))
 return loop if area>0 else list(reversed(loop))
def bridge(bm,a,b,new):
 a=ccw(a);b=ccw(b)
 # Align the two contours, then advance by normalized perimeter to avoid twisted seams.
 ai,bi=min(((i,j) for i in range(len(a)) for j in range(len(b))),key=lambda ij:(a[ij[0]].co-b[ij[1]].co).length)
 a=a[ai:]+a[:ai];b=b[bi:]+b[:bi]
 def fractions(v):
  lens=[(v[(i+1)%len(v)].co-v[i].co).length for i in range(len(v))];out=[0]
  for x in lens:out.append(out[-1]+x)
  return [x/out[-1] for x in out]
 fa,fb=fractions(a),fractions(b);i=j=0
 while i<len(a) or j<len(b):
  if j==len(b) or (i<len(a) and fa[i+1]<=fb[j+1]):
   vs=[a[i%len(a)],a[(i+1)%len(a)],b[j%len(b)]];i+=1
  else:vs=[a[i%len(a)],b[(j+1)%len(b)],b[j%len(b)]];j+=1
  new.append(bm.faces.new(vs))
reports={}
for level,file in enumerate(['production_master','round1_lod1','round1_lod2','round1_lod3']):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'review/round3/before/{file}.blend'))
 o=bpy.data.objects['Body'];me=o.data;original=[v.co.copy() for v in me.vertices];before=sum(len(f.vertices)-2 for f in me.polygons)
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();piece=bm.verts.layers.int['piece'];uv=bm.loops.layers.uv['UVMap'];head=bm.faces.layers.int['head'];deform=bm.verts.layers.deform.verify();names={g.name:g.index for g in o.vertex_groups}
 holes=components([e for e in bm.edges if e.is_boundary and all(v[piece]==0 and v.co.z<1.1 for v in e.verts)])
 assert len(holes)==3,(file,len(holes));loops=[ordered(es) for es in holes];top=max(loops,key=lambda vs:sum(v.co.z for v in vs)/len(vs));bottom=sorted([v for v in loops if v is not top],key=lambda vs:sum(v.co.x for v in vs)/len(vs))
 # Ring at upper hip and a shared crotch seam make a connected pair-of-pants surface.
 count=[24,12,12,8][level];ring=[];new=[]
 def vertex(co):
  v=bm.verts.new(co);v[piece]=0
  z=v.co.z;t=max(0,min(1,(1.015-z)/.23));left=max(0,min(1,.5+v.co.x/.20))
  weights={'B_Pelvis':1-t*.85,'B_L_Thigh':t*.85*left,'B_R_Thigh':t*.85*(1-left)}
  for n,w in weights.items():
   if w>1e-7:v[deform][names[n]]=w
  return v
 for i in range(count):
  angle=-math.pi/2+2*math.pi*i/count;direction=Vector((math.cos(angle),math.sin(angle),0));centre=Vector((0,.09,.875));hit=surface.ray_cast(centre,direction,.4)[0]
  assert hit is not None and abs(hit.x)<.33
  ring.append(vertex(hit))
 # The midline seam remains above the natural crotch and is shared by both legs.
 seam=[vertex((0,.15,.790)),vertex((0,.085,.785)),vertex((0,.02,.805))]
 positive=ring[:count//2+1]+seam
 negative=ring[count//2:]+ring[:1]+list(reversed(seam))
 bridge(bm,top,ring,new);bridge(bm,positive,bottom[1],new);bridge(bm,negative,bottom[0],new)
 # Orient from retained skin; leave accepted old normals/winding untouched.
 pending=set(new);known=set(bm.faces)-pending
 while pending:
  advanced=False
  for f in list(pending):
   shared=next(((loop,q) for loop in f.loops for q in loop.edge.link_faces if q in known),None)
   if shared:
    loop,q=shared;other=next(l for l in q.loops if l.edge==loop.edge)
    if other.vert==loop.vert:f.normal_flip()
    pending.remove(f);known.add(f);advanced=True
  assert advanced
 # The previous bake also left transparent/black texels on triangles spanning the cut rim.
 image=bpy.data.images.load(str(P/'textures/round1_rebaked/min1_body_basecolor.png'),check_existing=True)
 pixels=np.array(image.pixels[:]).reshape(1024,1024,4);remap=[]
 for f in bm.faces:
  if f in new or not all(v[piece]==0 and v.co.z<1.08 for v in f.verts) or max(v.co.z for v in f.verts)<.70:continue
  uvs=np.array([l[uv].uv[:] for l in f.loops]);assert len(uvs)==3
  samples=np.array([uvs[0]*i/12+uvs[1]*j/12+uvs[2]*(12-i-j)/12 for i in range(13) for j in range(13-i)])
  xy=np.clip((samples*1024).astype(int),0,1023);values=pixels[xy[:,1],xy[:,0]]
  if np.min(values[:,3])<.99 or np.min(values[:,:3].max(1))<.025:remap.append(f)
 for f in new:
  f[head]=0;f.material_index=0;f.smooth=True
 for f in new+remap:
  # Map each continuous triangle into opaque fur, without changing a texture pixel.
  f.normal_update();axis=max(range(3),key=lambda i:abs(f.normal[i]));coords=[i for i in range(3) if i!=axis]
  xy=np.array([[l.vert.co[i] for i in coords] for l in f.loops]);xy-=xy.min(0);size=max(float(xy.max()),.001);xy/=size
  for loop,point in zip(f.loops,xy):loop[uv].uv=((414+point[0]*47)/1024,1-(426+point[1]*43)/1024)
 assert not [e for e in bm.edges if e.is_boundary and all(v[piece]==0 and v.co.z<1.1 for v in e.verts)]
 bm.to_mesh(me);bm.free();me.update()
 assert all((v.co-original[i]).length<1e-7 for i,v in enumerate(me.vertices[:len(original)]))
 reports[file]={'level':level,'body_open_edges_below_belt_before':sum(len(e) for e in holes),'body_open_edges_below_belt_after':0,'triangles_before':before,'triangles_after':sum(len(f.vertices)-2 for f in me.polygons),'added_triangles':len(new),'existing_cut_rim_faces_with_empty_bake_remapped':len(remap),'original_vertices_unchanged':True,'maps_unchanged':True,'kilt':'Existing doubleSided material retained; hem and belt openings are intended.'}
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'));print('CLOSED_HIPS',file,reports[file],flush=True)
(P/'review/round3/repair.json').write_text(json.dumps(reports,indent=2))
