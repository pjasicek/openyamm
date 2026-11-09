"""Actual triangle crossings for the Thug shoulder shells; touching edges are permitted."""
import numpy as np
from mathutils.bvhtree import BVHTree
def hit(a,b):
 n=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]);result=np.zeros(len(a),bool)
 for j in range(3):
  start=a[:,j];end=a[:,(j+1)%3];d=end-start;den=(n*d).sum(1)
  t=np.divide((n*(b[:,0]-start)).sum(1),den,out=np.full(len(a),-1.),where=np.abs(den)>1e-12)
  q=start+t[:,None]*d
  e0=b[:,1]-b[:,0];e1=b[:,2]-b[:,0];qq=q-b[:,0]
  aa=(e0*e0).sum(1);bb=(e0*e1).sum(1);cc=(e1*e1).sum(1);dd=(qq*e0).sum(1);ee=(qq*e1).sum(1);det=aa*cc-bb*bb
  u=np.divide(cc*dd-bb*ee,det,out=np.full(len(a),-1.),where=det>1e-18)
  v=np.divide(aa*ee-bb*dd,det,out=np.full(len(a),-1.),where=det>1e-18)
  result|=(t>1e-5)&(t<1-1e-5)&(u>=-1e-5)&(v>=-1e-5)&(u+v<=1+1e-5)
 return result

def intersections(a, fa, b, fb):
 ta=BVHTree.FromPolygons(a.tolist(),fa.tolist(),all_triangles=True)
 tb=BVHTree.FromPolygons(b.tolist(),fb.tolist(),all_triangles=True)
 pairs=ta.overlap(tb)
 if not pairs:return []
 aa=a[fa[[i for i,j in pairs]]];bb=b[fb[[j for i,j in pairs]]]
 return [pairs[i] for i in np.where(hit(aa,bb)|hit(bb,aa))[0]]

def self_check():
 a=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
 b=np.array([[.25,.25,-1.],[.25,.25,1.],[.75,.25,0.]])
 f=np.array([[0,1,2]])
 assert intersections(a,f,b,f)
 assert not intersections(a,f,b+np.array([3.,0.,0.]),f)
 assert intersections(b,f,a,f)
self_check()
