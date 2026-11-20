"""Measured 10% reduction ladder with protected skull, bony hands and teeth."""
import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];O=P/'review/reduction';O.mkdir(exist_ok=True);sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;reference=body.copy();reference.data=body.data.copy();reference.name='Reference';sc.collection.objects.link(reference);original=body.data.copy();base=len(original.polygons);C=np.array([v.co[:] for v in original.vertices]);pa=np.array([v.value for v in original.attributes['part'].data]);fixed=np.where(((pa>0)&(pa<100))|(pa>100)|((pa==100)&(np.abs(C[:,0]+.014)<.075)&(C[:,1]<.005)&(C[:,2]>2.00)&(C[:,2]<2.16)))[0].tolist();reports=[]
def surface(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();verts=[v.co.copy() for v in m.vertices];tree=BVHTree.FromPolygons(verts,[list(f.vertices) for f in m.polygons],all_triangles=True);ev.to_mesh_clear();return verts,tree
for step in range(1,10):
 for attempt in range(3):
  body.data=original.copy();rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;g=body.vertex_groups.new(name='ReductionProtection');g.add(fixed,1,'REPLACE');mod=body.modifiers.new('Reduce','DECIMATE');mod.ratio=.9**step;mod.vertex_group=g.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);body.vertex_groups.remove(body.vertex_groups['ReductionProtection']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
  me=body.data;me.calc_loop_triangles();cv,ct=surface(body);protected=max(ct.find_nearest(original.vertices[i].co)[3] for i in fixed);errors=[];bad=set()
  for role,frame in [('Standing',1),('Attack',22),('Attack',46),('Death',61),('Dead',1)]:
   rig.animation_data.action=bpy.data.actions[role];sc.frame_set(frame);rv,rt=surface(reference);cv,ct=surface(body);errors.extend(rt.find_nearest(v)[3] for v in cv);errs=[ct.find_nearest(v)[3] for v in rv];errors.extend(errs);bad.update(int(i) for i in np.where(np.array(errs)>.006)[0])
   assert min(v.z for v in cv)>-.01,(step,role)
  if not bad:break
  if attempt<2:
   seeds=bad.copy()
   for edge in original.edges:
    if any(v in seeds for v in edge.vertices):bad.update(edge.vertices)
   fixed=sorted(set(fixed)|bad)
 row={'step':step,'protection_refinements':attempt,'triangles':len(me.loop_triangles),'original_triangles':base,'protected_vertices':len(fixed),'protected_max_error_mm':protected*1000,'posed_error_p95_p99_max_mm':(np.percentile(errors,[95,99,100])*1000).tolist()};reports.append(row);print(row,flush=True);assert protected<.0002,(step,protected)
 reference.hide_render=True;common.workbench_clay(sc);rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);common.render_views(str(O/f'step_{step:02d}'),1.1,2.7,views=('front','left'),resolution=(480,640));common.render_views(str(O/f'step_{step:02d}_head'),2.04,.48,views=('front',),resolution=(480,480))
 bpy.data.objects.remove(reference,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(O/f'step_{step:02d}.blend'));reference=body.copy();reference.data=original.copy();reference.name='Reference';sc.collection.objects.link(reference);reference.hide_render=True
 (O/'ladder.json').write_text(json.dumps(reports,indent=2))
 if row['triangles']<11000 or row['posed_error_p95_p99_max_mm'][2]>12:break
