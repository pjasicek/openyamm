"""Reduce broad surfaces while retaining the twelve actual hand/stone contact patches."""
from pathlib import Path
import sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.path[:0]=[str(repo/'tools'),str(p.parent/'claude_shared/gates')]
from build_actor_lods import generate
from run_gates import Glb,Mesh,grip_points
source=p/'export/mm8_m520_runtime_lod0.glb';g=Glb(source);ni=g.names['Cyclops'];m=Mesh(g,g.nodes[ni]['mesh'],ni,'Cyclops/colour0')
a=next(a for n,a,lo,hi in g.clips() if n=='Attack');pose=g.pose(a,np.array([.4]))[0];co=m.posed(pose)
stone=m.weight(['Boulder'])>.9;faces=m.faces[stone[m.faces].all(1)];tree=BVHTree.FromPolygons(co.tolist(),faces.tolist(),all_triangles=True)
protected=set();rows=[]
for side in 'LR':
 m.regions['hand_'+side]=m.select({'weights':[f'B_{side}_Hand',f'B_{side}_Finger*'],'weight_min':.3})
 tris,bary,groups,signature=grip_points(m,side,{})
 points=np.einsum('sk,tkj->tsj',bary,co[tris]).reshape(-1,3)
 hits=[tree.find_nearest(Vector(point)) for point in points];distance=np.array([v[3] for v in hits])
 for label,mask in zip(['palm']+[f'finger{i}' for i in range(5)],groups):
  indices=np.flatnonzero(mask);i=int(indices[np.argmin(distance[indices])]);hand_tri=tris[i//len(bary)];stone_tri=faces[hits[i][2]]
  protected.update(int(v) for v in hand_tri);protected.update(int(v) for v in stone_tri)
  rows.append({'side':side,'part':label,'gap_mm':float(distance[i]*1000),'hand_triangle':hand_tri.tolist(),'stone_triangle':stone_tri.tolist()})
# Keep the thin lower garment intact when simplifying the distant body.
cloth=m.select({'component_seeds':[[0,-.2,1.2]],'bounds':[[-.5,-.6,.87],[.5,.6,1.30]]})
protected.update(int(v) for v in np.flatnonzero(cloth))
hip_skin=(m.weight(['B_*_Thigh','B_*_Calf'])>.3)&(m.rest[:,2]>.95)&(m.rest[:,2]<1.4)
protected.update(int(v) for v in np.flatnonzero(hip_skin))
points=np.unique(np.round(m.rest[sorted(protected)],6),axis=0)
budgets={'Cyclops_A':(.61,.30,.205),'CyclopsHead_A':(.36,.13,.027),'Boulder_A':(.5,.22,.125)}
report={'material_ratios':budgets,'points':points.tolist(),'contacts':rows,'source':'Attack 0.4 s, full-detail surface samples','ratios':[.5,.22,.125]}
(p/'work/lod_contact_patches.json').write_text(json.dumps(report,indent=2));assert len(rows)==12
print('CONTACT_PATCHES',len(points),'vertices',sum(stone[list(protected)]),'stone indices',flush=True)
generate(source,p/'export/mm8_m520_lods.glb','Cyclops',ratios=(.5,.22,.125),protected_points=points,material_ratios=budgets)
