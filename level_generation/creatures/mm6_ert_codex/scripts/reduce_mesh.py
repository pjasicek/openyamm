"""Reduce after weighting; preserve face and fist contours, then compare posed surfaces."""
import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
old=body.copy();old.data=body.data.copy();scene.collection.objects.link(old);old.name='SourceDensity';old.hide_render=True
before=len(body.data.polygons)
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
dec=body.modifiers.new('Reduce','DECIMATE');dec.ratio=6000/before
bpy.ops.object.modifier_move_to_index(modifier=dec.name,index=0);bpy.ops.object.modifier_apply(modifier=dec.name)
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
assert not any(not e.is_manifold for e in bm.edges)
# Replace the folded skull cap locally; a manifold edge count alone cannot detect an inward fold.
bm.normal_update()
bad={f for f in bm.faces if f.calc_center_median().z>2.25 and f.normal.dot((f.calc_center_median()-Vector((-.035,0,2.16))).normalized())<0}
for _ in range(2):bad|={n for f in list(bad) for e in f.edges for n in e.link_faces}
if bad:
 bmesh.ops.delete(bm,geom=list(bad),context='FACES')
 boundary=[e for e in bm.edges if e.is_boundary]
 remaining=set(boundary);filled=[]
 while remaining:
  edge=next(iter(remaining));first,current=edge.verts;ordered=[first];remaining.remove(edge)
  while current!=first:
   ordered.append(current);following=[e for e in current.link_edges if e in remaining];assert len(following)==1
   edge=following[0];remaining.remove(edge);current=edge.other_vert(current)
  filled.append(bm.faces.new(ordered))
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 patched=bmesh.ops.poke(bm,faces=filled,center_mode='MEAN_WEIGHTED',offset=.003)
 deform=bm.verts.layers.deform.verify()
 for v in patched['verts']:
  v[deform].clear();v[deform][body.vertex_groups['B_Head'].index]=1.0
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 assert not any(not e.is_manifold for e in bm.edges)
bm.to_mesh(body.data);bm.free();body.data.update()
for v in body.data.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-6],key=lambda x:x[1],reverse=True)
 assert weights
 total=sum(w for _,w in weights[:8]);keep=dict(weights[:8])
 for gi,w in weights:
  if gi in keep:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
  else:body.vertex_groups[gi].remove([v.index])
report={'before':before,'after':len(body.data.polygons),'poses':{}}
def coordinates(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 co=[v.co.copy() for v in m.vertices];faces=[tuple(p.vertices) for p in m.polygons];ev.to_mesh_clear();return co,faces
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=old.color=(.55,.56,.57,1)
out=P/'review/reduction';out.mkdir(exist_ok=True)
for clip,t in [('Standing',0),('Walking',.4),('Attack',.9),('Hit',.16),('Death',.9),('Dead',0)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 f=t*30;scene.frame_set(math.floor(f),subframe=f%1)
 src,faces=coordinates(old);dst,dstfaces=coordinates(body);bvh=BVHTree.FromPolygons(dst,dstfaces,all_triangles=True)
 errors=np.array([bvh.find_nearest(v)[3] for v in src]);report['poses'][clip]={'mean_mm':float(errors.mean()*1000),'p99_mm':float(np.percentile(errors,99)*1000),'max_mm':float(errors.max()*1000)}
 print('POSE_DEVIATION',clip,report['poses'][clip])
 co=np.array(dst);centre=(co.min(0)+co.max(0))/2
 for label,ob in [('original',old),('reduced',body)]:
  old.hide_render=ob!=old;body.hide_render=ob!=body
  common.render_views(str(out/f'{clip}_{label}'),float(centre[2]),2.9 if clip not in ['Death','Dead'] else 3.3,views=('front','left','three_quarter'),resolution=(580,640),target=centre[:2])
old.hide_render=True;body.hide_render=False;bpy.data.objects.remove(old,do_unlink=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduced_v1.blend'))
(P/'work/reduction.json').write_text(json.dumps(report,indent=2));print('REDUCTION',json.dumps(report))
assert all(r['p99_mm']<35 for r in report['poses'].values()),report
