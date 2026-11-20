"""Remove the redundant skirt triangle discarded by Meshy; preserve vertices, weights and UVs."""
import bpy,bmesh,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src);body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);target=np.array([[.024322519,-.1480816007,.4414390326],[.0589174926,-.1609476507,.481122613],[.0428203903,-.1451430768,.5035305023]])
ids=[p.index for p in me.polygons if len(p.vertices)==3 and max(min(np.linalg.norm(co[v]-t) for v in p.vertices) for t in target)<1e-6]
assert len(ids)<=1,ids
if ids:
 f=me.polygons[ids[0]];vs=list(f.vertices);a,b,c=co[vs];covered=[]
 for q in me.polygons:
  if q.index==f.index or len(q.vertices)!=3:continue
  if sum(min(np.linalg.norm(co[v]-co[w]) for w in q.vertices)<1e-6 for v in vs)!=2:continue
  tri=co[list(q.vertices)];M=np.stack([tri[1]-tri[0],tri[2]-tri[0]],axis=1)
  uv=np.linalg.lstsq(M,(co[vs]-tri[0]).T,rcond=None)[0].T;err=np.linalg.norm(tri[0]+uv@M.T-co[vs],axis=1).max()
  bary=np.c_[1-uv.sum(1),uv]
  if err<.00005 and bary.min()>-.001 and q.area>f.area and abs(f.normal.dot(q.normal))>.99:covered.append((q.index,float(err)))
 assert len(covered)==1,covered
 bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[ids[0]]],context='FACES_ONLY');bm.to_mesh(me);bm.free()
 assert len(me.vertices)==len(co) and np.array_equal(co,np.array([v.co[:] for v in me.vertices]))
 print('SKIRT OVERLAP removed',ids[0],'covered within',covered[0][1],'m; vertices and weights retained',flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
