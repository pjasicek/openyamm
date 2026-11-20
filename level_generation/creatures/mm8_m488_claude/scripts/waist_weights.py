"""The flexible waistband follows the skin beneath it instead of a rigid pelvis transform."""
from pathlib import Path
import bpy,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
body=bpy.data.objects['Body'];me=body.data;me.calc_loop_triangles();piece=[a.value for a in me.attributes['piece'].data]
co=np.array([v.co[:] for v in me.vertices]);tri=[list(t.vertices) for t in me.loop_triangles if piece[t.vertices[0]]==0]
tree=BVHTree.FromPolygons(co.tolist(),tri,all_triangles=True)
for v in me.vertices:
 if piece[v.index]!=2 and not(piece[v.index]==1 and v.co.z>1.0):continue
 loc,normal,face,d=tree.find_nearest(v.co)
 a,b,c=co[tri[face]];weights=np.linalg.lstsq(np.c_[b-a,c-a],np.array(loc)-a,rcond=None)[0];bary=np.clip([1-weights.sum(),*weights],0,1);bary/=bary.sum()
 skin={}
 for vi,w in zip(tri[face],bary):
  for g in me.vertices[vi].groups:skin[g.group]=skin.get(g.group,0)+float(w)*g.weight
 alpha=1 if piece[v.index]==2 else float(np.clip((v.co.z-1.0)/.18,0,1));alpha=alpha*alpha*(3-2*alpha)
 old={g.group:g.weight for g in v.groups};mix={g:skin.get(g,0)*alpha+old.get(g,0)*(1-alpha) for g in skin.keys()|old.keys()}
 keep=sorted(mix.items(),key=lambda x:x[1],reverse=True)[:4];total=sum(w for g,w in keep)
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for g,w in keep:
  if w>1e-7:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
 assert abs(sum(g.weight for g in v.groups)-1)<1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
