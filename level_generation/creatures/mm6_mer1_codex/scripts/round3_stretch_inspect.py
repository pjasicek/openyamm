import bpy,sys,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));o=bpy.data.objects['Body'];g=G.Glb(P/'work/round3/pilot.glb');m=G.load_meshes(g)[0];kd=KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(v.co,v.index)
kd.balance();a=next(a for a in g.doc['animations']if a['name']=='Attack')
for t in [.4166667,1.0833333]:
 points=m.posed(g.pose(a,np.array([t]))[0]);ratios=np.linalg.norm(points[m.edges[:,0]]-points[m.edges[:,1]],axis=1)/m.lengths
 for j in np.argsort(ratios)[-12:]:
  coords=m.rest[m.edges[j]];ids=[kd.find(c)[1]for c in coords];print('EDGE',t,ratios[j],ids,coords.tolist(),[{o.vertex_groups[x.group].name:round(x.weight,3)for x in o.data.vertices[i].groups}for i in ids],flush=True)
