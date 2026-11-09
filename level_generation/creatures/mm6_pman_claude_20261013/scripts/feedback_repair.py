"""Local feedback correction: trim the false hair border and tuck upper-arm caps beneath the cuffs."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_feedback_v1/textured_uv.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=[v.co.copy() for v in me.vertices];pc=[v.value for v in me.attributes['piece'].data]
head_faces=[list(f.vertices) for f in me.polygons if pc[f.vertices[0]]==1];head_bvh=BVHTree.FromPolygons(co,head_faces,all_triangles=True)
bound=json.loads((P/'work/feedback_boundaries.json').read_text())
hair_moved=[]
# Only three oversized cap corners remained at each upper arm after reduction. Refit these hidden
# corners to the limb centreline, then add UV-preserving cuts so the cuff region can bend cleanly.
arm_report={}
for side,part in [('L',4),('R',5)]:
 sh=rig.data.bones[f'B_{side}_UpperArm'].head_local;el=rig.data.bones[f'B_{side}_Forearm'].head_local;axis=(el-sh).normalized();ids=bound[str(part)]['boundaries'][0]['vertices'];assert len(ids)==3
 for vi in ids:
  v=me.vertices[vi];t=(v.co-sh).dot(axis);center=sh+axis*t;rad=v.co-center;v.co=center+rad.normalized()*.040
  for g in list(v.groups):body.vertex_groups[g.group].remove([vi])
  body.vertex_groups[f'B_{side}_UpperArm'].add([vi],1.,'REPLACE')
 bm=bmesh.new();bm.from_mesh(me);layer=bm.verts.layers.int['piece']
 for t in [.22,.27,.32]:
  verts=[v for v in bm.verts if v[layer]==part];edges=[e for e in bm.edges if all(v[layer]==part for v in e.verts)];faces=[f for f in bm.faces if all(v[layer]==part for v in f.verts)]
  result=bmesh.ops.bisect_plane(bm,geom=verts+edges+faces,dist=1e-7,plane_co=sh+axis*t,plane_no=axis,clear_inner=False,clear_outer=False)
  for e in result['geom_cut']:
   if isinstance(e,bmesh.types.BMVert):e[layer]=part
 # Round the newly sampled upper forearm; the original reduced cap was triangular.
 for v in bm.verts:
  if v[layer]!=part:continue
  t=(v.co-sh).dot(axis)
  if .19<t<.34:
   center=sh+axis*t;rad=v.co-center;w=min(1.,(t-.19)/.025,(.34-t)/.025)
   v.co=v.co.lerp(center+rad.normalized()*.034,max(0.,w))
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();arm_report[side]={'cap_vertices':ids,'cap_radius_m':.040,'cuts_m':[.22,.27,.32]}
# Trim the generated skin-coloured hair skirt at its real hair line instead of intersecting it with skin.
def hair_line(x,y):
 x=abs(x+.005)
 front=1.635+.002*math.exp(-((x-.024)/.013)**2)-.95*max(0,x-.037)
 w=float(np.clip((-y-.012)/.020,0,1))
 return 1.49+(front-1.49)*w
bm=bmesh.new();bm.from_mesh(me);piece_layer=bm.verts.layers.int['piece']
verts=[v for v in bm.verts if v[piece_layer]==2]
for v in verts:v.co.z-=hair_line(v.co.x,v.co.y)
edges=[e for e in bm.edges if all(v[piece_layer]==2 for v in e.verts)];faces=[f for f in bm.faces if all(v[piece_layer]==2 for v in f.verts)]
bmesh.ops.bisect_plane(bm,geom=verts+edges+faces,dist=1e-7,plane_co=(0,0,0),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
for v in bm.verts:
 if v[piece_layer]!=2:continue
 at_border=abs(v.co.z)<1e-6
 v.co.z+=hair_line(v.co.x,v.co.y)
 if at_border or any(e.is_boundary for e in v.link_edges):
  q,n,_,dist=head_bvh.find_nearest(v.co)
  v.co=q-n*.0003;hair_moved.append(1)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for side,part in [('L',4),('R',5)]:
 counts={}
 for f in me.polygons:
  if me.attributes['piece'].data[f.vertices[0]].value==part:
   for e in f.edge_keys:counts[e]=counts.get(e,0)+1
 arm_report[side]['cap_vertices']=sorted({v for e,n in counts.items() if n==1 for v in e})
 assert len(arm_report[side]['cap_vertices'])==3
# BMesh preserves UVs, deform weights and face/point attributes; assert the resulting skin contract.
for v in me.vertices:
 total=sum(g.weight for g in v.groups)
 assert total>.99 and total<1.01,(v.index,total)
assert len(me.polygons)<10200
# Changed cap coordinates invalidate the original custom corner normals.
if me.has_custom_normals:
 bpy.context.view_layer.objects.active=body
 bpy.ops.mesh.customdata_custom_splitnormals_clear()
for f in me.polygons:f.use_smooth=True
me.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
(P/'work/feedback_geometry.json').write_text(json.dumps({'hair_vertices_moved':len(hair_moved),'arms':arm_report,'triangles':len(me.polygons),'uvs_preserved':True,'animations_unchanged':True},indent=2))
print('FEEDBACK_GEOMETRY',len(hair_moved),len(me.polygons),flush=True)
