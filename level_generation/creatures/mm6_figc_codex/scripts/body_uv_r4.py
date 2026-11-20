"""Carry each LOD's original UV-chart lineage into the single packed LOD0 atlas."""
import sys,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
sys.path.insert(0,str(P.parent/'claude_shared/gates'));from run_gates import Glb
source=Glb(R/'before/mm6_figc.glb');a=np.load(R/'body_packed.npz');faces=a['faces'];packed=a['packed_uv'];labels=a['chart'];reports=[];results={'0':packed}
def lineage(level):
 old=np.load(R/f'body_source_uv{level}.npz');points=old['pos'][old['faces']];kd=KDTree(len(points))
 for i,p in enumerate(points.mean(1)):kd.insert(Vector(p),i)
 kd.balance();pr=source.doc['meshes'][level]['primitives'][0];pos=source.accessor(pr['attributes']['POSITION']);tri=source.accessor(pr['indices']).reshape(-1,3).astype(int);uv=[];charts=[];errors=[]
 for f in tri:
  p=pos[f];near=kd.find_n(Vector(p.mean(0)),8)
  def score(row):
   return sum(min(np.linalg.norm(q-point) for q in points[row[1]]) for point in p)
  match=min(near,key=score)[1];order=[int(np.argmin(np.linalg.norm(points[match]-point,axis=1))) for point in p];error=max(np.linalg.norm(p-points[match][order],axis=1));assert error<2e-5,(level,error)
  errors.append(error);uv.append(old['uv'][match][order]);charts.append(int(old['chart'][match]))
 reports.append({'lod':level,'source_geometry_match_max_m':float(max(errors))});return np.array(uv),np.array(charts)
uv0,chart0=lineage(0);trees={};indices={};physical=BVHTree.FromPolygons([Vector(p) for p in a['pos']],faces.tolist(),all_triangles=True)
def tree(key,ids):
 indices[key]=ids;points=[Vector((*u,0)) for f in uv0[ids] for u in f];trees[key]=BVHTree.FromPolygons(points,np.arange(len(points)).reshape(-1,3).tolist(),all_triangles=True)
for c in np.unique(chart0):tree(int(c),np.flatnonzero(chart0==c))
for label in np.unique(labels):tree(('packed',int(label)),np.flatnonzero(labels==label))
for level in range(1,4):
 uv,chart=lineage(level);out=[];distances=[];missing=[];prim=source.doc['meshes'][level]['primitives'][0];positions=source.accessor(prim['attributes']['POSITION']);triangles=source.accessor(prim['indices']).reshape(-1,3).astype(int)
 for f,(t,c) in enumerate(zip(uv,chart)):
  if int(c) not in trees:
   # These islands vanished from LOD0 during its earlier independent collapse; explicitly project those faces.
   points=positions[triangles[f]];hit,n,sf,distance=physical.find_nearest(Vector(points.mean(0)));mapped=[]
   for p in points:
    q=barycentric_transform(hit,*[Vector(x) for x in a['pos'][faces[sf]]],*[Vector((*u,0)) for u in packed[sf]]);mapped.append(tuple(q.xy))
   out.append(packed[sf]);missing.append(int(c));continue
  hit,n,i,dist=trees[int(c)].find_nearest(Vector((*t.mean(0),0)));sf=int(indices[int(c)][i]);key=('packed',int(labels[sf]));mapped=[]
  for p in t:
   hit,n,i,dist=trees[key].find_nearest(Vector((*p,0)));sf=int(indices[key][i]);q=barycentric_transform(hit,*[Vector((*u,0)) for u in uv0[sf]],*[Vector((*u,0)) for u in packed[sf]])
   mapped.append(tuple(q.xy));distances.append(dist)
  mapped=np.array(mapped)
  if abs(np.cross(mapped[1]-mapped[0],mapped[2]-mapped[0]))<1e-12:mapped=packed[sf].mean(0)+(packed[sf]-packed[sf].mean(0))*.01
  out.append(mapped)
 results[str(level)]=np.array(out);reports[-1].update(lost_source_chart_faces=len(missing),lost_source_charts=sorted(set(missing)),uv_projection_p99=float(np.percentile(distances,99)),uv_projection_max=float(max(distances)))
 assert np.isfinite(results[str(level)]).all()
np.savez(R/'body_uvs.npz',**results);(R/'body_uv_transfer.json').write_text(json.dumps(reports,indent=2));print('BODY_UV_LINEAGE',reports,flush=True)
