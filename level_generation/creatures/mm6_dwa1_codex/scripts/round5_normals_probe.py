import bpy,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];source=None
for path in ['work/round4_before/work/export_reimport.blend','work/round5/step6.blend','work/round5/baked6/candidate.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));ob=bpy.data.objects['Body'];me=ob.data;me.calc_loop_triangles();xyz=np.array([v.co[:]for v in me.vertices]);tri=np.array([t.vertices for t in me.loop_triangles]);loops=np.array([t.loops for t in me.loop_triangles]);n=np.array([x.vector[:]for x in me.corner_normals]);g=np.cross(xyz[tri[:,1]]-xyz[tri[:,0]],xyz[tri[:,2]]-xyz[tri[:,0]]);g/=np.maximum(np.linalg.norm(g,axis=1,keepdims=True),1e-12);dot=(g*n[loops].mean(1)).sum(1);print('NORMAL_PROBE',path,'matrix',list(ob.matrix_world),'triangles',len(tri),'dot',np.percentile(dot,[0,1,10,50,99]),'negative',int((dot<0).sum()),flush=True)
 if source is None:source=BVHTree.FromPolygons(xyz.tolist(),tri.tolist(),all_triangles=True)
 else:print('NEAREST',np.percentile([source.find_nearest(v.co)[3]for v in me.vertices],[50,90,99,100]),flush=True)
