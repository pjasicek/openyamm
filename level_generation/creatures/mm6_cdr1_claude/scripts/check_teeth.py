import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=o.data
ids=[x.value for x in me.attributes['tooth_id'].data];rows={t['id']:t['row'] for t in json.loads((P/'review/teeth_v2/geometry.json').read_text())['teeth']};faces={row:[list(f.vertices) for f in me.polygons if rows.get(ids[f.index])==row] for row in ['upper','lower']}
for row,fs in faces.items():
 group=o.vertex_groups['Head' if row=='upper' else 'Jaw'].index
 for i in {v for f in fs for v in f}:assert len(me.vertices[i].groups)==1 and me.vertices[i].groups[0].group==group and me.vertices[i].groups[0].weight==1
errors=[];samples=0;maximum_edge_error=0
edges={tuple(sorted((a,b))) for fs in faces.values() for f in fs for a,b in zip(f,f[1:]+f[:1])};lengths={e:(me.vertices[e[0]].co-me.vertices[e[1]].co).length for e in edges}
for action in bpy.data.actions:
 rig.animation_data.action=action;lo,hi=action.frame_range
 for i in range(int(lo*2),int(hi*2)+1):
  sc.frame_set(i//2,subframe=(i%2)*.5);em=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=em.to_mesh();co=[v.co.copy() for v in mesh.vertices];em.to_mesh_clear();trees={row:BVHTree.FromPolygons(co,fs,all_triangles=False,epsilon=0) for row,fs in faces.items()};overlap=trees['upper'].overlap(trees['lower']);samples+=1
  if overlap:errors.append({'clip':action.name,'frame':i/2,'overlapping_faces':len(overlap)})
  maximum_edge_error=max(maximum_edge_error,max(abs((co[a]-co[b]).length-l) for (a,b),l in lengths.items()))
report={'samples':samples,'upper_lower_intersections':errors,'maximum_tooth_edge_length_error_m':maximum_edge_error,'rigid_bone_weights':True};(P/'review/teeth_v2/motion_check.json').write_text(json.dumps(report,indent=2)+'\n');print('TOOTH CHECK',report);assert not errors;assert maximum_edge_error<2e-6
