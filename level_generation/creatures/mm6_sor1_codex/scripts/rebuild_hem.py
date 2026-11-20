import bpy,bmesh,math,json,sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));body=bpy.data.objects['Body'];me=body.data
assert not body.get('hem_rebuilt'), 'Run from original step1 only'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1_before_hem.blend'))
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);tree=BVHTree.FromPolygons(co.tolist(),[tuple(f.vertices) for f in me.polygons if all(pv[i]==100 for i in f.vertices)])
N=80;Z=np.linspace(.125,1.125,28);R=np.zeros((len(Z),N));center=np.array([0,-.02])
for j,z in enumerate(Z):
 for k in range(N):
  a=2*math.pi*k/N;d=Vector((math.sin(a),math.cos(a),0));start=Vector((*center,z));hits=[];t=0
  while t<.6:
   loc,n,idx,dl=tree.ray_cast(start+d*(t+1e-5),d,.6-t)
   if loc is None:break
   hits.append(loc);t+=dl+1e-5
  if hits:R[j,k]=(hits[-1]-start).length
  else:
   ids=np.where((pv==100)&(abs(co[:,2]-z)<.055))[0];angles=np.arctan2(co[ids,0],co[ids,1]+.02);da=np.abs((angles-a+math.pi)%(2*math.pi)-math.pi);near=ids[da<.08]
   if len(near):R[j,k]=float(np.linalg.norm(co[near,:2]-center,axis=1).max())
   else:
    assert j==len(Z)-1,(j,k)
    R[j,k]=R[j-1,k]  # Continue the open top rim beneath the belt.
# Preserve folds, remove isolated triangular spikes in the longitudinal section.
for _ in range(2):
 for j in range(1,len(Z)-1):R[j]=.7*R[j]+.15*(R[j-1]+R[j+1])
bm=bmesh.new();bm.from_mesh(me);pv_layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pv_layer]>=100],context='VERTS')
rings=[]
for j,z in enumerate(Z):
 ring=[]
 for k in range(N):
  a=2*math.pi*k/N;v=bm.verts.new((R[j,k]*math.sin(a),center[1]+R[j,k]*math.cos(a),z));v[pv_layer]=100;ring.append(v)
 rings.append(ring)
for lower,upper in zip(rings,rings[1:]):
 for k in range(N):bm.faces.new((lower[k],upper[k],upper[(k+1)%N],lower[(k+1)%N]))
# Original generated soles contained interior bridges. Closed low leather shoes are rebuilt under the opaque hem.
for sign,piece in [(-1,101),(1,102)]:
 rings=[]
 for z,rx,ry,cy in [(0,.041,.090,-.038),(.012,.047,.096,-.038),(.05,.043,.092,-.035),(.085,.034,.062,-.01),(.19,.029,.034,.006)]:
  ring=[]
  for k in range(16):
   a=2*math.pi*k/16;x=rx*math.cos(a);y=cy+ry*math.sin(a)
   turn=sign*math.radians(-9);xx=x*math.cos(turn)-y*math.sin(turn);yy=x*math.sin(turn)+y*math.cos(turn)
   v=bm.verts.new((sign*.16+xx,yy,z));v[pv_layer]=piece;ring.append(v)
  rings.append(ring)
 for lower,upper in zip(rings,rings[1:]):
  for k in range(16):bm.faces.new((lower[k],lower[(k+1)%16],upper[(k+1)%16],upper[k]))
 bm.faces.new(tuple(reversed(rings[0])));bm.faces.new(tuple(rings[-1]))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bmesh.ops.triangulate(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
for f in me.polygons:f.use_smooth=True
co=np.array([v.co[:] for v in me.vertices]);me.attributes['orig_co'].data.foreach_set('vector',co.ravel())
body['hem_rebuilt']=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/clean_v3'),.85,1.9,views=('front','left','back'),resolution=(600,900))
print('REBUILT robe',N,len(Z),'shoes separate; tris',sum(len(f.vertices)-2 for f in me.polygons))
