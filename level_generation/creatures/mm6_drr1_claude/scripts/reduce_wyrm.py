"""Protected 10% reductions, checked against the animated master at keys and subframes."""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];O=P/'review/reduction';O.mkdir(exist_ok=True)
reports=[]
for step in range(1,11):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master_v2.blend'))
 body=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];sc=bpy.context.scene;me=body.data
 reference=body.copy();reference.data=me.copy();sc.collection.objects.link(reference)
 fixed=set();names={g.index:g.name for g in body.vertex_groups}
 for f in me.polygons:
  if f.material_index==1:fixed.update(f.vertices)
 for v in me.vertices:
  if sum(g.weight for g in v.groups if 'Paw' in names[g.group])>.5:fixed.add(v.index)
 first={}
 for l in me.loops:
  u=me.uv_layers.active.data[l.index].uv;i=l.vertex_index
  if i in first and (u-first[i]).length>1e-6:fixed.add(i)
  first.setdefault(i,u.copy())
 bm=bmesh.new();bm.from_mesh(me)
 for e in bm.edges:
  if len(e.link_faces)==2 and e.calc_face_angle()>math.radians(80):fixed.update(v.index for v in e.verts)
 bm.free();protected=[me.vertices[i].co.copy() for i in fixed]
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 g=body.vertex_groups.new(name='Keep');g.add(list(fixed),1,'REPLACE')
 mod=body.modifiers.new('Reduce','DECIMATE');mod.ratio=.9**step;mod.vertex_group='Keep';mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);body.vertex_groups.remove(body.vertex_groups["Keep"])
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 def surf(obj):
  e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=[x.co.copy() for x in m.vertices];f=[list(x.vertices) for x in m.polygons];e.to_mesh_clear();return v,BVHTree.FromPolygons(v,f,all_triangles=True)
 result={'step':step,'ratio':.9**step,'triangles':len(body.data.polygons),'protected':len(fixed),'clips':{},'passed_numeric':True}
 for a in bpy.data.actions:
  rig.animation_data.action=a;lo,hi=a.frame_range;errors=[];low=1e9
  for f in np.linspace(lo,hi,13):
   sc.frame_set(int(f),subframe=f%1);rv,rt=surf(reference);cv,ct=surf(body)
   errors.extend(ct.find_nearest(v)[3] for v in rv);errors.extend(rt.find_nearest(v)[3] for v in cv);low=min(low,min(v.z for v in cv))
  stats=np.percentile(errors,[95,99,100])*1000;result['clips'][a.name]={'surface_mm_p95_p99_max':stats.tolist(),'min_z':low,'samples':13}
  if stats[1]>1 or stats[2]>3 or low<-.002:result['passed_numeric']=False
 bpy.data.objects.remove(reference,do_unlink=True);rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'step_{step:02d}.blend'))
 (O/f'step_{step:02d}.json').write_text(json.dumps(result,indent=2)+'\n');reports.append(result)
 (O/'ladder.json').write_text(json.dumps(reports,indent=2)+'\n');print('STEP',step,result['triangles'],result['passed_numeric'],flush=True)
 if not result['passed_numeric']:break
