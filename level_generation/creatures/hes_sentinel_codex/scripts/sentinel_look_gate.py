"""Barrel/base clearance at the runtime target-look limits on the final authoring mesh."""
import json,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/sentinel_final_rig.blend'))
rig=bpy.data.objects['SentinelRig'];body=bpy.data.objects['Sentinel'];rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis.identity()
def rigid(vi,name):
 return any(g.group==body.vertex_groups[name].index and g.weight>.9999 for g in body.data.vertices[vi].groups)
base=[list(f.vertices) for f in body.data.polygons if all(rigid(v,'B_Root') for v in f.vertices)]
bar=[list(f.vertices) for f in body.data.polygons if all(rigid(v,'B_Recoil') for v in f.vertices)]
report={};rest=rig.data.bones['B_Barrel'].matrix_local.to_3x3().inverted();pb=rig.pose.bones['B_Barrel'];pb.rotation_mode='QUATERNION'
for yaw in [0]:
 for pitch in [-25,30]:
  pb.rotation_quaternion=Quaternion((rest@Vector((0,0,1))).normalized(),math.radians(yaw))@Quaternion((rest@Vector((1,0,0))).normalized(),math.radians(-pitch))
  bpy.context.view_layer.update();o=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();co=[v.co.copy() for v in m.vertices]
  n=len(BVHTree.FromPolygons(co,base).overlap(BVHTree.FromPolygons(co,bar)));o.to_mesh_clear();assert n==0,(yaw,pitch,n)
  report[f'yaw{yaw}_pitch{pitch}']={'barrel_base_intersections':n}
(P/'review/sentinel_look_gate.json').write_text(json.dumps(report,indent=2)+'\n');print('RUNTIME LOOK CLEARANCE PASS',flush=True)
