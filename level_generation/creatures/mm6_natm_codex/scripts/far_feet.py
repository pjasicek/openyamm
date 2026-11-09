import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));C.activate('Standing',0);o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();high=np.array([v.co[:]for v in mm.vertices]);mm.calc_loop_triangles();ht=np.array([t.vertices[:]for t in mm.loop_triangles]);hp=np.array([x.value for x in o.data.attributes['piece'].data]);skin=ht[np.all(hp[ht]==0,axis=1)];tree=BVHTree.FromPolygons([Vector(x)for x in high],skin.tolist(),all_triangles=True);ev.to_mesh_clear()
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_continuous.blend'));C.activate('Standing',0);r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pos=np.array([v.co[:]for v in mm.vertices]);ev.to_mesh_clear();pv=np.array([x.value for x in me.attributes['piece'].data]);gn={g.index:g.name for g in o.vertex_groups};ids=[v.index for v in me.vertices if pv[v.index]==0 and any('Foot'in gn[g.group]or'Toe'in gn[g.group]for g in v.groups if g.weight>.3)]
print('FOOT_COORDS',[(i,list(pos[i]),me.vertices[i].co[:])for i in ids],flush=True)
for v in me.vertices:
 if v.index not in ids:continue
 p=Vector(pos[v.index]);q,n,_,d=tree.find_nearest(p);delta=q-p
 # A sole patch remains flat. Preserve horizontal outline while restoring the original standing sole plane.
 if v.co.z<.035:delta.z=.001-pos[v.index,2]
 M=np.zeros((3,3))
 for g in v.groups:
  if gn[g.group]in r.data.bones:M+=np.array((r.pose.bones[gn[g.group]].matrix@r.data.bones[gn[g.group]].matrix_local.inverted()).to_3x3())*g.weight
 v.co+=Vector(np.linalg.solve(M,np.array(delta)))
me.update();C.reset();dest=P/'work/lod3_feet.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));render(dest,P/'review/reduction/lod3_feet',P/'work/reduction/lod3_continuous',88)
