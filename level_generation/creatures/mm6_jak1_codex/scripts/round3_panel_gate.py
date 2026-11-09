"""Signed outer-panel test for the split, overlapping wrap; all runtime colour LODs at 48 Hz."""
import sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as shared

def covered(tree,p,ray):
 hit,normal,_,_=tree.ray_cast(p+ray*.0001,ray,.6)
 return hit is not None and normal.dot(ray)>0
probe=BVHTree.FromPolygons([(x,y,z)for x in [0,.02]for y,z in [(-1,-1),(1,-1),(1,1),(-1,1)]],[(0,1,2,3),(4,5,6,7)])
assert covered(probe,Vector((.01,0,0)),Vector((1,0,0)))
assert not covered(probe,Vector((.03,0,0)),Vector((1,0,0)))
assert probe.ray_cast(Vector((.03,0,1.02)),Vector((-1,0,0)),.05)[0] is None
assert probe.ray_cast(Vector((.03,0,0)),Vector((-1,0,0)),.05)[0] is not None
g=shared.Glb(P/'export/mm6_jak1.glb');rows=[]
for mesh in shared.load_meshes(g):
 if '/shadow' in mesh.label:continue
 co=mesh.rest;mesh.find_components(); choices=[]
 for component in np.unique(mesh.components):
  ids=mesh.components==component;points=co[ids];lo=points.min(0);hi=points.max(0)
  if .5<lo[2]<.8 and 1.0<hi[2]<1.2 and hi[0]-lo[0]>.4:choices.append(ids)
 assert len(choices)==1,(mesh.label,len(choices));cloth=choices[0]
 faces=mesh.faces[cloth[mesh.faces].all(1)];tri=co[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 radial=tri.mean(1);radial[:,2]=0;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-12);faces=faces[(normal*radial).sum(1)>.25]
 skin=np.flatnonzero((~cloth)&(mesh.weight(['B_*_Thigh'])>.3)&(co[:,2]>.67)&(co[:,2]<1.04))
 assert len(faces)>=8 and len(skin)>=4,(mesh.label,len(faces),len(skin))
 def signed(points,limit=.05):
  tree=BVHTree.FromPolygons(points.tolist(),faces.tolist());out={}
  for i in skin:
   point=Vector(points[i]);loc,n,fi,d=tree.find_nearest(point,limit)
   if loc is None:continue
   v=point-loc;outside=v.length>1e-6 and v.dot(n)>0 and v.normalized().dot(n)>math.cos(math.pi/4)
   if outside and covered(tree,point,v.normalized()):outside=False
   if outside:
    # Beyond a hem edge is an allowed exit; an inward ray must actually cross fabric.
    hit,hn,_,hd=tree.ray_cast(point,-n,.05)
    outside=hit is not None and hn.dot(n)>.25
    if outside:d=hd
   out[i]=(outside,d,fi)
  return out
 baseline=signed(co,1.0);eligible={i for i,(outside,d,fi)in baseline.items() if not outside};assert eligible,(mesh.label,'empty coverage')
 for name,a,lo,hi in g.clips():
  times=np.r_[np.arange(lo,hi,1/48),hi];poses=g.pose(a,times);worst=(0.,None,None)
  for t,pose in zip(times,poses):
   for i,(outside,d,fi)in signed(mesh.posed(pose)).items():
    if i in eligible and outside and d>worst[0]:worst=(float(d),float(t),int(i))
  row={'mesh':mesh.label,'clip':name,'hz':48,'outer_triangles':len(faces),'covered_skin_samples':len(eligible),'depth_mm':worst[0]*1000,'seconds':worst[1],'vertex':worst[2],'pass':worst[0]<=.002};rows.append(row);print(row,flush=True)
(P/'review/round3/outer_panel_gate.json').write_text(json.dumps({'method':'Signed nearest outward panel; initially covered skin only; overlapping outer panels preserve coverage. No artificial cap across the split hem.','rows':rows,'pass':all(r['pass']for r in rows)},indent=2))
assert all(r['pass']for r in rows)
