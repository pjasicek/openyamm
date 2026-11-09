"""Fit a clean dedicated head and bridge it to the retained body neck before rigging."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json,math
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_clean.blend'))
with bpy.data.libraries.load(str(p/'work/head_selected.blend'),link=False) as (src,dst):
 dst.objects=['HeadSource']
head=dst.objects[0];bpy.context.collection.objects.link(head)
for o in bpy.data.objects:o.select_set(o is head)
bpy.context.view_layer.objects.active=head
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
scale=.45/(hi[2]-lo[2]);head.scale=(scale,)*3
head.location=(-float((lo[0]+hi[0])/2)*scale,-float((lo[1]+hi[1])/2)*scale,2.4-float(hi[2])*scale)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
head.data.materials.clear();mat=bpy.data.materials.new('HeadClay');mat.diffuse_color=(.65,.53,.43,1);head.data.materials.append(mat)
body=bpy.data.objects['P00']
for ob,cut,inside in [(body,1.95,False),(head,2.015,True)]:
 bm=bmesh.new();bm.from_mesh(ob.data)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,cut),plane_no=(0,0,1),clear_inner=inside,clear_outer=not inside)
 if ob is body:
  todo=set(bm.faces);parts=[]
  while todo:
   f=todo.pop();stack=[f];part=[f]
   while stack:
    f=stack.pop()
    for e in f.edges:
     for n in e.link_faces:
      if n in todo:todo.remove(n);stack.append(n);part.append(n)
   parts.append(part)
  removed=[]
  for part in parts:
   verts={v for f in part for v in f.verts}
   if min(v.co.z for v in verts)>1.75 and min(v.co.y for v in verts)>-.15:
    removed.extend(part)
  print('LEGACY_HAIR_REMOVED',len(removed),'components',len(parts),flush=True)
  if removed:bmesh.ops.delete(bm,geom=removed,context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(ob.data);bm.free()
for ob in [o for o in bpy.data.objects if o.type=='MESH']:
 if 'piece' not in ob.data.attributes:ob.data.attributes.new('piece','INT','POINT')
 ob.data.attributes.new('head','INT','FACE').data.foreach_set('value',[int(ob is head)]*len(ob.data.polygons))
 for f in ob.data.polygons:f.use_smooth=True
 ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];pv=bm.verts.layers.int['piece']
rings=[]
for cut in [1.95,2.015]:
 ring=[v for v in bm.verts if abs(v.co.z-cut)<1e-5 and any(e.is_boundary for e in v.link_edges)]
 assert len(ring)>8,(cut,len(ring))
 assert all(sum(e.is_boundary and abs(e.other_vert(v).co.z-cut)<1e-5 for e in v.link_edges)==2 for v in ring),(cut,'branched neck')
 todo=set(ring);loops=[]
 while todo:
  start=todo.pop();loop=[start]
  while True:
   candidates=[e.other_vert(loop[-1]) for e in loop[-1].link_edges if e.is_boundary and e.other_vert(loop[-1]) in todo]
   if not candidates:break
   v=candidates[0];todo.remove(v);loop.append(v)
  loops.append(loop)
 print('NECK_LOOPS',cut,[{'vertices':len(loop),'bounds':[[min(v.co[k] for v in loop) for k in range(3)],[max(v.co[k] for v in loop) for k in range(3)]]} for loop in loops],flush=True)
 loops.sort(key=len,reverse=True);ring=loops[0]
 # Smaller cuts are the ends of legacy neck/hair strands inside the main neck opening.
 for extra in loops[1:]:
  centre=bm.verts.new(sum((v.co for v in extra),Vector())/len(extra))
  for i,v in enumerate(extra):
   f=bm.faces.new([v,extra[(i+1)%len(extra)],centre]);f[hd]=int(cut>2)
 area=sum(v.co.x*ring[(i+1)%len(ring)].co.y-ring[(i+1)%len(ring)].co.x*v.co.y for i,v in enumerate(ring))
 if area<0:ring.reverse()
 centre=sum((v.co for v in ring),Vector())/len(ring)
 start=min(range(len(ring)),key=lambda i:math.atan2(ring[i].co.y-centre.y,ring[i].co.x-centre.x))
 ring=ring[start:]+ring[:start];rings.append(ring)
lo,hi=rings

def parameters(ring):
 lengths=[(ring[(i+1)%len(ring)].co-v.co).length for i,v in enumerate(ring)];total=sum(lengths);params=[0]
 for length in lengths:params.append(params[-1]+length/total)
 return params

lp,hp=parameters(lo),parameters(hi);mid=[]
for i,v in enumerate(lo):
 k=min(len(hi)-1,int(np.searchsorted(hp,lp[i],side='right')-1));t=(lp[i]-hp[k])/(hp[k+1]-hp[k])
 point=v.co.lerp(hi[k].co.lerp(hi[(k+1)%len(hi)].co,t),.5)
 point.z+=.04*float(np.clip((abs(point.x)-.16)/.10,0,1));mid.append(bm.verts.new(point))
bridges=[]
for lower,upper in [(lo,mid),(mid,hi)]:
 aps,bps=parameters(lower),parameters(upper);i=j=0
 while i<len(lower) or j<len(upper):
  an=aps[i+1] if i<len(lower) else float('inf');bn=bps[j+1] if j<len(upper) else float('inf')
  if an<bn:vs=[lower[i%len(lower)],lower[(i+1)%len(lower)],upper[j%len(upper)]];i+=1
  else:vs=[lower[i%len(lower)],upper[(j+1)%len(upper)],upper[j%len(upper)]];j+=1
  f=bm.faces.new(vs);f[hd]=0;f.material_index=0;f.smooth=True;bridges.append(f)
assert not any(e.is_boundary for v in lo+hi for e in v.link_edges),'unclosed neck'
neck=[v for v in bm.verts if v[pv]==0 and 1.93<v.co.z<2.035]
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=neck,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
report={'neck_ring_vertices':[len(lo),len(hi)],'triangles':len(bm.faces),'neck_bridge_triangles':len(bridges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
bm.to_mesh(body.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_fitted.blend'))
(p/'work/head_fit.json').write_text(json.dumps(report,indent=2));print('HEAD_FIT',report)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_fitted_body'),1.2,3.1,views=('front','left','back','three_quarter'),resolution=(600,900))
common.render_views(str(p/'review/head_fitted_close'),2.15,.68,views=('front','left','back','three_quarter'),resolution=(650,650))
