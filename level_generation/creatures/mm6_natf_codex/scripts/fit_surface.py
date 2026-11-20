"""Fit coarse triangle interiors to the source surface to recover volume lost by collapse."""
import numpy as np,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def fit(ob,ref,level):
 if level<2:return
 src=ref.data;me=ob.data;src.calc_loop_triangles();me.calc_loop_triangles();sp=np.array([a.value for a in src.attributes['piece'].data]);pp=np.array([a.value for a in me.attributes['piece'].data]);S=np.array([tuple(v.co)for v in src.vertices]);C=np.array([tuple(v.co)for v in me.vertices]);orig=C.copy();tri=np.array([t.vertices[:]for t in src.loop_triangles]);faces=np.array([t.vertices[:]for t in me.loop_triangles]);trees={int(p):BVHTree.FromPolygons([Vector(v)for v in S],tri[sp[tri[:,0]]==p].tolist(),all_triangles=True)for p in np.unique(sp)};limit=.012 if level==2 else .025;basis=np.array([[1/3]*3,[.5,.5,0],[0,.5,.5],[.5,0,.5]])
 for iteration in range(5):
  delta=np.zeros_like(C);weights=np.zeros(len(C))
  for f in faces:
   tree=trees[int(pp[f[0]])]
   for bary in basis:
    q=bary@C[f];h,n,ix,d=tree.find_nearest(Vector(q));offset=np.array(h)-q
    if d>limit*2:continue
    for j in range(3):delta[f[j]]+=offset*bary[j];weights[f[j]]+=bary[j]
  C+=.65*delta/np.maximum(weights,1e-8)[:,None];dv=C-orig;length=np.linalg.norm(dv,axis=1);C=orig+dv*np.minimum(1,limit/np.maximum(length,1e-8))[:,None];C[:,2]=np.maximum(C[:,2],0)
 for v,co in zip(me.vertices,C):v.co=co
 me.update();print('SURFACE_FIT',ob.name,level,float(np.linalg.norm(C-orig,axis=1).max()),flush=True)
