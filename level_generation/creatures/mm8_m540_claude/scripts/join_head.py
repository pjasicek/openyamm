"""Join the corrected head to the retained neck with one welded surface and unchanged body UVs/rig."""
from pathlib import Path
import bpy,bmesh,sys,json,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_body.blend'))
with bpy.data.libraries.load(str(p/'work/head_fitted.blend'),link=False) as (src,dst):dst.objects=['HeadSource']
bpy.context.collection.objects.link(dst.objects[0])
bpy.data.objects['Body'].data.attributes.new('head','INT','FACE')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];source=bpy.data.objects['HeadSource'];rig.animation_data_create();rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
original=body.copy();original.data=body.data.copy();original.name='OriginalBody';bpy.context.collection.objects.link(original)
head=source.copy();head.data=source.data.copy();head.name='ReplacementHead';bpy.context.collection.objects.link(head)
for o in bpy.context.view_layer.objects:o.select_set(o is head)
bpy.context.view_layer.objects.active=head
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(head.data);bm.free()
# Keep the detailed head until the deformation and per-region reduction checks.
for f in head.data.polygons:f.use_smooth=True
head.data.uv_layers.active.name='HeadUV';head.data.uv_layers.new(name='UVMap',do_init=True)
for i,u in enumerate(head.data.uv_layers['HeadUV'].data):head.data.uv_layers['UVMap'].data[i].uv=u.uv
BODY_CUT=1.345;HEAD_CUT=1.355
q=lambda v:v.co.z-.2*v.co.y
# Both rings are beneath the jaw. Remove the old head entirely, including UV-split faces and misplaced tusks.
bm=bmesh.new();bm.from_mesh(body.data);pv=bm.verts.layers.int['piece'];hd=bm.faces.layers.int['head']
fs=[f for f in bm.faces if all(v[pv]==0 for v in f.verts)];geom=set(fs)|{e for f in fs for e in f.edges}|{v for f in fs for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=(0,0,BODY_CUT),plane_no=(0,-.2,1))
doomed=[f for f in bm.faces if (all(v[pv]==0 for v in f.verts) and sum(q(v) for v in f.verts)/len(f.verts)>BODY_CUT-1e-6) or any(v[pv] in [6,7,8,11,12] for v in f.verts)]
bmesh.ops.delete(bm,geom=doomed,context='FACES')
for f in bm.faces:f[hd]=0
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(body.data);bm.free()
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if v.co.z-.2*v.co.y<1.42],dist=.001);bmesh.ops.dissolve_degenerate(bm,dist=.0003,edges=[e for e in bm.edges if all(v.co.z-.2*v.co.y<1.42 for v in e.verts)]);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,HEAD_CUT),plane_no=(0,-.2,1),clear_inner=True)
# The cut exposes a sub-millimetre UV seam at the rear neck.
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if abs(q(v)-HEAD_CUT)<1e-5],dist=.001)
bm.to_mesh(head.data);bm.free()
# Transfer head/neck weights by nearest original skin triangle, preserving the fitted skeleton.
om=original.data;om.calc_loop_triangles();oldtris=[t for t in om.loop_triangles if all(om.attributes['piece'].data[i].value==0 for i in t.vertices) and min(om.vertices[i].co.z for i in t.vertices)>1.27]
otree=BVHTree.FromPolygons([v.co for v in om.vertices],[tuple(t.vertices) for t in oldtris],all_triangles=True)
for g in body.vertex_groups:head.vertex_groups.new(name=g.name)
for v in head.data.vertices:
 loc,n,fi,d=otree.find_nearest(v.co);t=oldtris[fi];abc=[om.vertices[i].co for i in t.vertices]
 bc=barycentric_transform(loc,*abc,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));weights={}
 for idx,w in zip(t.vertices,bc):
  for e in om.vertices[idx].groups:weights[e.group]=weights.get(e.group,0)+max(0,w)*e.weight
 weights={i:w for i,w in weights.items() if w>.002};total=sum(weights.values());assert total>.1
 for i,w in weights.items():head.vertex_groups[i].add([v.index],w/total,'REPLACE')
head.data.attributes.new('piece','INT','POINT');head.data.attributes.new('head','INT','FACE');head.data.attributes['head'].data.foreach_set('value',[1]*len(head.data.polygons))
for o,name in [(body,'BodyClay'),(head,'HeadClay')]:
 o.data.materials.clear();o.data.materials.append(bpy.data.materials.new(name))
 for f in o.data.polygons:f.material_index=0;f.use_smooth=True
source.hide_render=True;source.hide_set(True);original.hide_render=True;original.hide_set(True)
for o in bpy.context.view_layer.objects:o.select_set(o in [body,head])
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
# Bridge unequal vertex counts in angular order; the existing ring vertices belong to both regions.
bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];uv=bm.loops.layers.uv['HeadUV'];buv=bm.loops.layers.uv['UVMap']
rings=[]
for cut in [BODY_CUT,HEAD_CUT]:
 ring=[v for v in bm.verts if abs(q(v)-cut)<1e-5 and any(e.is_boundary for e in v.link_edges)]
 assert len(ring)>8,(cut,len(ring))
 print('NECK_RING',cut,len(ring),[(tuple(v.co),sum(e.is_boundary and abs(q(e.other_vert(v))-cut)<1e-5 for e in v.link_edges),[round(q(e.other_vert(v)),6) for e in v.link_edges if e.is_boundary]) for v in ring if sum(e.is_boundary and abs(q(e.other_vert(v))-cut)<1e-5 for e in v.link_edges)!=2],flush=True)
 assert all(sum(e.is_boundary and abs(q(e.other_vert(v))-cut)<1e-5 for e in v.link_edges)==2 for v in ring)
 # Follow actual boundary edges; angular sorting crosses small neck folds.
 start=min(ring,key=lambda v:math.atan2(v.co.y+.04,v.co.x+.018));ordered=[start]
 while True:
  nxt=[e.other_vert(ordered[-1]) for e in ordered[-1].link_edges if e.is_boundary and e.other_vert(ordered[-1]) in ring and (len(ordered)==1 or e.other_vert(ordered[-1]) is not ordered[-2])]
  v=nxt[0]
  if v is start:break
  assert v not in ordered,'neck boundary branch'
  ordered.append(v)
 assert len(ordered)==len(ring),(len(ordered),len(ring))
 area=sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(ordered,ordered[1:]+ordered[:1]))
 if area<0:ordered=[ordered[0]]+list(reversed(ordered[1:]))
 rings.append(ordered)
for f in bm.faces:
 if f[hd]:
  for l in f.loops:l[uv].uv.y*=.94
lo,hi=rings;angle=lambda v:math.atan2(v.co.y+.04,v.co.x+.018)
huv={v:next(l[uv].uv.copy() for l in v.link_loops if l.face[hd]) for v in hi}
# New neck faces extend the sampled head-neck texture to the body's shared edge.
for v in lo:huv[v]=huv[min(hi,key=lambda w:abs(math.atan2(math.sin(angle(v)-angle(w)),math.cos(angle(v)-angle(w)))))]
def arc(ring):
 lengths=[(ring[(i+1)%len(ring)].co-v.co).length for i,v in enumerate(ring)]
 return np.cumsum(lengths)/sum(lengths)
la,ha=arc(lo),arc(hi)
i=j=0;bridges=[]
while i<len(lo) or j<len(hi):
 an=la[i] if i<len(lo) else float('inf')
 bn=ha[j] if j<len(hi) else float('inf')
 if an<bn:vs=[lo[i%len(lo)],lo[(i+1)%len(lo)],hi[j%len(hi)]];i+=1
 else:vs=[lo[i%len(lo)],hi[(j+1)%len(hi)],hi[j%len(hi)]];j+=1
 f=bm.faces.new(vs);f[hd]=1;f.material_index=1;f.smooth=True;bridges.append(f)
 us=[(angle(l.vert)+math.pi)/(2*math.pi) for l in f.loops]
 if max(us)-min(us)>.5:us=[1.0 if u<.5 else u for u in us]
 for l,u in zip(f.loops,us):l[uv].uv=(.02+.96*u,.985 if l.vert in lo else .958)
# The generated neck contains tiny dangling triangles on an otherwise closed surface.
spurs=[f for f in bm.faces if all(1.32<q(v)<1.42 for v in f.verts) and sum(e.is_boundary for e in f.edges)>=2 and any(len(e.link_faces)>2 for e in f.edges)]
assert all(f.calc_area()<.0001 for f in spurs)
if spurs:bmesh.ops.delete(bm,geom=spurs,context='FACES')
print('NECK_SPURS_REMOVED',len(spurs),flush=True)
assert not any(e.is_boundary for v in lo+hi for e in v.link_edges),'unclosed neck'
pv=bm.verts.layers.int['piece']
neck=[v for v in bm.verts if v[pv]==0 and 1.325<q(v)<1.375 and not (v.co.y<-.08 and v.co.z>1.36)]
for _ in range(4):bmesh.ops.smooth_vert(bm,verts=neck,factor=.45,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
rows=[]
for e in bm.edges:
 if len(e.link_faces)!=2 or e.link_faces[0][hd]==e.link_faces[1][hd]:continue
 b,h=sorted(e.link_faces,key=lambda f:f[hd])
 for t in [0,.25,.5,.75,1]:
  row={'pos':list(e.verts[0].co.lerp(e.verts[1].co,t))}
  for name,f,u in [('body',b,buv),('head',h,uv)]:
   ls=[next(l for l in f.loops if l.vert==v) for v in e.verts];centre=sum((l[u].uv for l in f.loops),Vector((0,0)))/len(f.loops)
   row[name]=list(ls[0][u].uv.lerp(ls[1][u].uv,t).lerp(centre,.025))
  rows.append(row)
bm.to_mesh(body.data);bm.free();body.data.update();bpy.data.objects.remove(original,do_unlink=True)
(p/'review/geometry/head_seam_samples.json').write_text(json.dumps(rows)+'\n')
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/geometry/head_join_clay'),1.50,.48,views=('front','left','back','three_quarter'),resolution=(600,600))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_head.blend'))
report={'total_triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'head_triangles':sum(len(f.vertices)-2 for f in body.data.polygons if body.data.attributes['head'].data[f.index].value),'neck_samples':len(rows),'neck_boundary_vertices':[len(lo),len(hi)],'reason':'Original full-body head has no tusk surfaces and a narrow flat muzzle; a connected replacement preserves the required silhouette and mouth anatomy','route':'Replacement head, welded neckline, UV carry-over, nearest-face interpolated original skin weights'}
(p/'review/geometry/head_join.json').write_text(json.dumps(report,indent=2)+'\n');print('HEAD_GRAFT',report)
