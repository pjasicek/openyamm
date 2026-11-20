"""Measure inter-chart boundary clearance, rather than xatlas's scaled padding setting."""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];uv=np.load(P/'work/packed_uv.npz')['uv'];edges=defaultdict(list);parent=list(range(len(uv)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for fi,tri in enumerate(uv):
 for j in range(3):edges[tuple(sorted((tuple(tri[j]),tuple(tri[(j+1)%3]))))].append(fi)
for faces in edges.values():
 for f in faces[1:]:parent[root(f)]=root(faces[0])
boundary=[(e,root(fs[0])) for e,fs in edges.items() if len(fs)==1];seg=np.array([e for e,c in boundary]);chart=np.array([c for e,c in boundary]);mid=seg.mean(1);length=np.linalg.norm(seg[:,1]-seg[:,0],axis=1);tree=cKDTree(mid);threshold=16/2048;best=threshold
for i,(a,b) in enumerate(seg):
 for point in (a,b):
  ix=np.array(tree.query_ball_point(point,length.max()/2+threshold));ix=ix[chart[ix]!=chart[i]]
  if not len(ix):continue
  ab=seg[ix,1]-seg[ix,0];ap=point-seg[ix,0];t=np.clip((ap*ab).sum(1)/(ab*ab).sum(1),0,1)
  best=min(best,float(np.linalg.norm(ap-t[:,None]*ab,axis=1).min()))
assert 8/2048<=best<threshold,best*2048
r={'charts':len(set(root(i) for i in range(len(uv)))),'boundary_edges':len(seg),'minimum_gap_texels_2k':best*2048,'method':'exact vertex-to-boundary-segment distance across distinct disjoint charts; bounded spatial search','note':'uv_pack.minimum_chart_padding_texels_2k was scaled single padding, not the distance between chart boundaries'}
(P/'review/geometry/uv_gutter.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
