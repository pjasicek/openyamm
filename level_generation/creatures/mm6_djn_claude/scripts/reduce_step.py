"""One protected 10% ladder step, always derived from the accepted weighted/UV master."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1];OUT=P/'review/reduction';step=json.loads((OUT/'next_step.json').read_text())['step'];ratio=.9**step;label=f'step_{step:02d}'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data;baseline=len(me.polygons)
reference=body.copy();reference.data=me.copy();reference.name='Reference';sc.collection.objects.link(reference)
fixed=set();names={g.index:g.name for g in body.vertex_groups}
for f in me.polygons:
 if f.material_index==1:fixed.update(f.vertices)
for v in me.vertices:
 if sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['Hand','Finger','Thumb','Index','Middle','Ring','Pinky','Toe','Foot']))>.25:fixed.add(v.index)
first_uv={};uv=me.uv_layers.active
for loop in me.loops:
 v=loop.vertex_index;u=uv.data[loop.index].uv
 if v in first_uv and (u-first_uv[v]).length>1e-6:fixed.add(v)
 first_uv.setdefault(v,u.copy())
fixed_coords=[me.vertices[i].co.copy() for i in fixed]
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
protect=body.vertex_groups.new(name='ReductionProtection');protect.add(list(fixed),1.,'REPLACE')
mod=body.modifiers.new('Reduce','DECIMATE');mod.ratio=ratio;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);body.vertex_groups.remove(body.vertex_groups['ReductionProtection'])
bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
me=body.data;me.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons],all_triangles=True)
protected_error=max(tree.find_nearest(v)[3] for v in fixed_coords)
assert len(me.materials)==2 and protected_error<.0001,(len(me.materials),protected_error)
for v in me.vertices:
 w=[g.weight for g in v.groups if g.weight>1e-6];assert len(w)<=4 and abs(sum(w)-1)<1e-5
assert all(math.isfinite(x) and -.001<x<1.001 for u in me.uv_layers.active.data for x in u.uv)
def surface(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();verts=[v.co.copy() for v in m.vertices];faces=[list(f.vertices) for f in m.polygons];e.to_mesh_clear();return verts,BVHTree.FromPolygons(verts,faces,all_triangles=True)
report={'step':step,'ratio':ratio,'triangles':len(me.loop_triangles),'baseline_triangles':baseline,'protected_vertices':len(fixed),'protected_surface_error_mm':protected_error*1000,'material_triangles':[sum(t.material_index==i for t in me.loop_triangles) for i in range(2)],'clips':{}}
for a in bpy.data.actions:
 rig.animation_data.action=a;lo,hi=a.frame_range;errors=[];minz=1e9
 frames=sorted(set(np.linspace(lo,hi,9).tolist()+([f+1 for f in range(33,47)] if a.name=='Attack' else [])))
 for f in frames:
  sc.frame_set(int(f),subframe=f%1);rv,rt=surface(reference);cv,ct=surface(body)
  errors.extend(rt.find_nearest(v)[3] for v in cv);errors.extend(ct.find_nearest(v)[3] for v in rv);minz=min(minz,min(v.z for v in cv))
 report['clips'][a.name]={'surface_mm_p95_p99_max':(np.percentile(errors,[95,99,100])*1000).tolist(),'minimum_z':minz,'samples':len(frames)}
 assert minz>-.006,(a.name,minz)
bpy.data.objects.remove(reference,do_unlink=True);rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{label}.blend'))

(OUT/f'{label}.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCTION',json.dumps(report),flush=True)
import sys
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
common.workbench_clay(sc)
for role,frame in [('Standing',1),('Attack',24),('Death',23)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(frame);common.render_views(str(OUT/f'{label}_{role}'),1.1,2.7,views=('front','three_quarter'),resolution=(480,640))
