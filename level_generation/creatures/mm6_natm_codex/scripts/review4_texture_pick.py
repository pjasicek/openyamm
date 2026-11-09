import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
import bpy
def pixels(name):
 im=bpy.data.images.load(str(P/f'export/textures_shared/body/{name}.png'));im.colorspace_settings.name='Non-Color';w,h=im.size;return np.array(im.pixels[:]).reshape(h,w,4)[::-1]*255
g=S.Glb(P/'export/mm6_natm.glb');m=S.load_meshes(g)[0];a=next(a for a in g.doc['animations']if a['name']=='Standing');pose=g.pose(a,np.array([0.]))[0];points=m.posed(pose);tree=BVHTree.FromPolygons(points.tolist(),m.faces.tolist(),all_triangles=True);d=g.doc;pr=d['meshes'][m.index]['primitives'][0];uv=g.accessor(pr['attributes']['TEXCOORD_0']);maps=[pixels(n)for n in ['basecolor','metal_rough','normal','region_mask']]
for px,py in [(640,350),(648,357),(630,353),(483,475),(483,489),(590,486),(231,540),(705,512),(710,495)]:
 origin=Vector(((px-500)*.95/1000,-5,1.32+(425-py)*.95/1000));loc,n,fi,dist=tree.ray_cast(origin,Vector((0,1,0)));ids=m.faces[fi];tri=points[ids];w=np.linalg.lstsq(np.vstack([tri.T,np.ones(3)]),np.r_[loc,1],rcond=None)[0];tex=w@uv[ids];values=[]
 for im in maps:
  yy,xx=np.minimum(np.array(im.shape[:2])-1,np.maximum(0,np.array([tex[1]*im.shape[0],tex[0]*im.shape[1]]).astype(int)));values.append(im[yy,xx].tolist())
 print('TEX',px,py,'rest',m.rest[ids].mean(0).tolist(),'uv',tex.tolist(),'maps',values,flush=True)
