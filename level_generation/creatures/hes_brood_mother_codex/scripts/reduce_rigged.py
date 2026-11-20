"""Reduce the weighted mesh; preserve face, fingers and arm deformation bands."""
import bpy
import json
import sys
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
ratio=float(sys.argv[sys.argv.index('--')+1]);tag=str(round(ratio*100))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
body=bpy.data.objects['BroodMother'];me=body.data
old=np.array([tuple(v.co) for v in me.vertices]);oldfaces=[tuple(f.vertices) for f in me.polygons]
tree=BVHTree.FromPolygons(old.tolist(),oldfaces,all_triangles=True)
names={g.index:g.name for g in body.vertex_groups}
group=body.vertex_groups.new(name='_protect')
for v in me.vertices:
 if sum(g.weight for g in v.groups if names.get(g.group,'').startswith('B_'))>.05:
  group.add([v.index],1.,'REPLACE')
for ob in bpy.context.scene.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('Reduction','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
mod.vertex_group=group.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
bpy.ops.object.modifier_apply(modifier=mod.name)
body.vertex_groups.remove(body.vertex_groups['_protect'])
newtree=BVHTree.FromPolygons([tuple(v.co) for v in body.data.vertices],
                            [tuple(f.vertices) for f in body.data.polygons],all_triangles=True)
d1=np.array([tree.find_nearest(v.co)[3] for v in body.data.vertices])
d2=np.array([newtree.find_nearest(p)[3] for p in old])
report={'ratio':ratio,'queen_before':len(oldfaces),'queen_after':len(body.data.polygons),
 'total_triangles':sum(sum(len(f.vertices)-2 for f in ob.data.polygons) for ob in bpy.context.scene.objects if ob.type=='MESH'),
 'surface_distance_p99_m':float(np.percentile(np.r_[d1,d2],99)),
 'surface_distance_max_m':float(max(d1.max(),d2.max()))}
(P/f'review/reduction_{tag}.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/reduced_{tag}.blend'))
print(json.dumps(report))
