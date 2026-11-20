"""Remove only sampled all-pose occluded triangles; retain contact/deformation surfaces and source corner normals."""
import bpy,bmesh,json,math,itertools,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3';prefix=os.environ.get('FIGC_HIDDEN_PREFIX','hidden');bpy.ops.wm.open_mainfile(filepath=os.environ.get('FIGC_HIDDEN_SOURCE',str(R/'before/work/final_motion.blend')));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;dirs=[Vector(v).normalized() for v in itertools.product([-1,0,1],repeat=3) if v!=(0,0,0)];report={}
def posed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return c
for part in ['Body','Axe','Shield']:
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();o=bpy.data.objects[part];me=o.data
 if part=='Body':
  for f in me.polygons:f.use_smooth=True
 me.calc_loop_triangles();faces=[tuple(t.vertices) for t in me.loop_triangles];before=len(faces);protected=set();rest=[v.co.copy() for v in me.vertices]
 if part=='Body':
  names=[g.name for g in o.vertex_groups];pv=[a.value for a in me.attributes['piece'].data]
  for v in me.vertices:
   if pv[v.index] in [1,2] or (pv[v.index]==0 and v.co.z>1.47) or any(g.weight>.2 and any(k in names[g.group] for k in ['UpperArm','Forearm','Hand','Finger']) for g in v.groups):protected.add(v.index)
 else:
  for v in me.vertices:
   if (v.co-rig.data.bones[part].head_local).length<.045:protected.add(v.index)
 candidates={i for i,f in enumerate(faces) if not any(v in protected for v in f)};initial=len(candidates);samples=0
 def visit(C):
  global candidates,samples
  tree=BVHTree.FromPolygons(C,faces,all_triangles=True);visible=set()
  for i in candidates:
   vs=[C[v] for v in faces[i]];center=sum(vs,Vector())/3;points=[center]+[v.lerp(center,.02) for v in vs]+[(a+b).lerp(center*2,.02)*.5 for a,b in zip(vs,vs[1:]+vs[:1])]
   for p in points:
    found=False
    for d in dirs:
     hit,n,fi,dist=tree.ray_cast(p+d*4,-d,4.0002)
     if hit is None or (hit-p).length<.0002:visible.add(i);found=True;break
    if found:break
  candidates-=visible;samples+=1
 visit(posed(o));print('HIDDEN_REST',part,len(candidates),'of',before,flush=True)
 if part=='Body':
  for role in ['Attack','Death','Running','Walking','Fidget','Hit','Standing','Dead']:
   a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
   for frame in np.arange(0,float(a.frame_range[1])+.001,.625):scene.frame_set(int(frame),subframe=float(frame%1));visit(posed(o))
   print('HIDDEN_CLIP',role,len(candidates),flush=True)
 # A polygon is removed only when every triangle in its tessellation stayed occluded.
 poly_tris={}
 for i,t in enumerate(me.loop_triangles):poly_tris.setdefault(t.polygon_index,[]).append(i)
 remove={p for p,ts in poly_tris.items() if all(i in candidates for i in ts)};normals={f.index:{tuple(round(x,7) for x in me.vertices[me.loops[li].vertex_index].co):tuple(me.corner_normals[li].vector) for li in f.loop_indices} for f in me.polygons};attr=me.attributes.new('_original_face','INT','FACE');attr.data.foreach_set('value',list(range(len(me.polygons))))
 bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bm.to_mesh(me);bm.free();custom=[]
 for f in me.polygons:
  fi=me.attributes['_original_face'].data[f.index].value;f.use_smooth=True
  for li in f.loop_indices:custom.append(normals[fi][tuple(round(x,7) for x in me.vertices[me.loops[li].vertex_index].co)])
 me.normals_split_custom_set(custom);after=sum(len(f.vertices)-2 for f in me.polygons);report[part]={'before':before,'after':after,'removed':before-after,'sampled_poses':samples,'view_directions':len(dirs),'samples_per_triangle':7,'protected_vertices':len(protected)};print('HIDDEN_REMOVAL',part,report[part],flush=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(R/f'{prefix}_clean.blend'));(R/f'{prefix}_faces.json').write_text(json.dumps(report,indent=2)+'\n')
