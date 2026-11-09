import bpy,json,numpy as np
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=o.data
me.calc_loop_triangles();rest=np.array([v.co[:] for v in me.vertices]);tri=list(me.loop_triangles)
wi=[t for t in tri if t.material_index==2 and np.abs(rest[list(t.vertices),0]).min()>.12]
bi=[t for t in tri if t.material_index!=2];report={};names={g.index:g.name for g in o.vertex_groups}
for clip,frame in [('Standing',0),('Standing',16),('Attack',30),('Death',16),('Death',24),('Dead',0)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[v.co.copy() for v in em.vertices];ev.to_mesh_clear()
 wt=BVHTree.FromPolygons(co,[list(t.vertices) for t in wi],all_triangles=True);bt=BVHTree.FromPolygons(co,[list(t.vertices) for t in bi],all_triangles=True)
 hits=wt.overlap(bt);ids=sorted({v for a,b in hits for v in bi[b].vertices});report[clip+str(frame)]={'triangle_pairs':len(hits),'vertices':[{'i':int(i),'rest':rest[i].tolist(),'posed':list(co[i]),'weights':{names[g.group]:g.weight for g in me.vertices[i].groups}} for i in ids]}
(P/'review/wing_contacts.json').write_text(json.dumps(report,indent=2)+'\n');print({k:{'pairs':v['triangle_pairs'],'vertices':len(v['vertices'])} for k,v in report.items()})
