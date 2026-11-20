import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/native_pilots_v1.blend'))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];scene=bpy.context.scene
groups={name:{v.index for v in body.data.vertices if any(body.vertex_groups[w.group].name==name for w in v.groups)} for name in ['Component_0','Component_3','Component_7','Component_15']}
skin=set.union(*(groups[n] for n in ['Component_0','Component_3','Component_7']))
skin_faces=[f.vertices[:] for f in body.data.polygons if all(i in skin for i in f.vertices)]
cloth_faces=[f.vertices[:] for f in body.data.polygons if all(i in groups['Component_15'] for i in f.vertices) and sum(body.data.vertices[i].co.z for i in f.vertices)/len(f.vertices)<.79]
def contains(tree,point):
    counts=[]
    for direction in [Vector((1,.137,.013)).normalized(),Vector((-1,.173,.011)).normalized()]:
        origin=point.copy();hits=0
        for _ in range(48):
            location,normal,index,distance=tree.ray_cast(origin,direction)
            if index is None:break
            hits+=1;origin=location+direction*.00001
        counts.append(hits%2==1)
    return all(counts)
report=[]
action=bpy.data.actions['Walk'];arm.animation_data.action=action;arm.animation_data.action_slot=action.slots[0]
for frame in range(1,38):
 scene.frame_set(frame);mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;co=[v.co.copy() for v in mesh.vertices];tree=BVHTree.FromPolygons(co,skin_faces,all_triangles=True)
 bad=[]
 for ids in cloth_faces:
  for point in [sum((co[i] for i in ids),co[0]*0)/len(ids)]+[co[i] for i in ids]:
   nearest,normal,index,dist=tree.find_nearest(point)
   signed=(point-nearest).dot(normal)
   if signed<-.003 and contains(tree,point):bad.append({'point':list(point),'signed_distance_m':signed,'nearest_skin_bones':[[body.vertex_groups[w.group].name for w in body.data.vertices[i].groups if w.weight>.2 and body.vertex_groups[w.group].name in arm.data.bones] for i in skin_faces[index]]})
 report.append({'frame':frame,'probes_inside_skin':len(bad),'worst':sorted(bad,key=lambda x:x['signed_distance_m'])[:3]})
(P/'review/cloth_surface_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('Worst cloth probes',sorted(report,key=lambda x:-x['probes_inside_skin'])[:4],flush=True)
