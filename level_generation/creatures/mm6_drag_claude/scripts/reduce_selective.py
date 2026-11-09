"""One protected 10% ladder step, always derived from the accepted weighted/UV master."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1];OUT=P/'review/reduction_v4';step=json.loads((OUT/"next_step.json").read_text())["step"];ratio=json.loads((OUT/"next_step.json").read_text()).get("ratio",.9**step);label=f'step_{step:02d}'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/accepted_v3.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data;me.calc_loop_triangles();baseline=len(me.loop_triangles)
reference=body.copy();reference.data=me.copy();reference.name='Reference';sc.collection.objects.link(reference)
fixed=set();names={g.index:g.name for g in body.vertex_groups}
for f in me.polygons:
 if f.material_index==1 and any(me.attributes['part'].data[v].value not in (1,2) for v in f.vertices):fixed.update(f.vertices)
for v in me.vertices:
 if me.attributes['part'].data[v.index].value not in (0,1,2):fixed.add(v.index)
 if sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['Foot']))>.25:fixed.add(v.index)
# Keep the volume-bearing hips/legs and small arms; reduce torso and tail surfaces instead.
for v in me.vertices:
 if v.co.z < .42 and v.co.y < .025:fixed.add(v.index)
 if abs(v.co.x)<.055 and me.attributes['part'].data[v.index].value in (1,2):fixed.add(v.index)
 if abs(v.co.x)<.02 and v.co.y>.025:fixed.add(v.index)
 if v.co.z > .54 and me.attributes['part'].data[v.index].value==0:fixed.add(v.index)
 if sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['Hand','ForeArm']))>.15:fixed.add(v.index)
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
me=body.data;me.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons],all_triangles=False)
protected_error=max(tree.find_nearest(v)[3] for v in fixed_coords)
assert len(me.materials)==2 and protected_error<.0001,(len(me.materials),protected_error)
for v in me.vertices:
 w=[g.weight for g in v.groups if g.weight>1e-6];assert len(w)<=4 and abs(sum(w)-1)<1e-5
assert all(math.isfinite(x) and -.001<x<1.001 for u in me.uv_layers.active.data for x in u.uv)
def surface(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();verts=[v.co.copy() for v in m.vertices];faces=[list(f.vertices) for f in m.polygons];e.to_mesh_clear();return verts,BVHTree.FromPolygons(verts,faces,all_triangles=False)
report={'step':step,'ratio':ratio,'triangles':len(me.loop_triangles),'baseline_triangles':baseline,'protected_vertices':len(fixed),'protected_surface_error_mm':protected_error*1000,'material_triangles':[sum(t.material_index==i for t in me.loop_triangles) for i in range(2)],'clips':{},'failed_checks':[]}
for a in bpy.data.actions:
 rig.animation_data.action=a;lo,hi=a.frame_range;errors=[];minz=1e9;worst={'error_mm':0}
 frames=sorted(set(np.linspace(lo,hi,5).tolist()+([f/2 for f in range(28,42)] if a.name in ('Attack','Cast') else [])))
 for f in frames:
  sc.frame_set(int(f),subframe=f%1);rv,rt=surface(reference);cv,ct=surface(body)
  for vertices,tree in [(cv,rt),(rv,ct)]:
   for v in vertices:
    error=tree.find_nearest(v)[3];errors.append(error)
    if error*1000>worst['error_mm']:worst={'error_mm':error*1000,'frame':float(f),'position':list(v)}
  minz=min(minz,min(v.z for v in cv))
 report['clips'][a.name]={'surface_mm_p95_p99_max':(np.percentile(errors,[95,99,100])*1000).tolist(),'minimum_z':minz,'samples':len(frames),'worst':worst}
 if minz<=-.006:report['failed_checks'].append({'clip':a.name,'check':'floor_clearance','minimum_z':minz,'limit':-.006})
bpy.data.objects.remove(reference,do_unlink=True);rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{label}.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o==body or o==rig or o.name=='DeathFlames' or o.name.startswith('Socket_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/f'{label}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
if any(v['surface_mm_p95_p99_max'][2]>7 for v in report['clips'].values()):report['failed_checks'].append({'check':'posed_surface_error','limit_mm':7})
(OUT/f'{label}.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCTION',json.dumps(report),flush=True)

