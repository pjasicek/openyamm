"""Nearest-surface rebake on separate garment pieces; MikkTSpace high/low normal conversion."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];out=p/'review/round4';size=4096
def arrays(obj):
 original=obj.data;original.calc_loop_triangles();tri=list(original.loop_triangles);oldloops=[i for t in tri for i in t.loops];indices=[t.vertices[:] for t in tri];normal=[original.corner_normals[i].vector[:] for i in oldloops];uvs=[original.uv_layers['UVMap'].data[i].uv[:] for i in oldloops]
 me=bpy.data.meshes.new('Exact rendered triangles');me.from_pydata([v.co[:] for v in original.vertices],[],indices);layer=me.uv_layers.new(name='UVMap')
 for corner,uv in zip(layer.data,uvs):corner.uv=uv
 for face in me.polygons:face.use_smooth=True
 me.normals_split_custom_set(normal);pv=me.attributes.new('piece','INT','POINT');pv.data.foreach_set('value',[v.value for v in original.attributes['piece'].data]);cf=me.attributes.new('cuff','INT','FACE');cf.data.foreach_set('value',[original.attributes['cuff'].data[t.polygon_index].value for t in tri]);obj.data=me
 me=obj.data;me.calc_loop_triangles();me.calc_tangents(uvmap='UVMap');tri=list(me.loop_triangles);ids=np.array([t.vertices[:] for t in tri]);loops=np.array([t.loops[:] for t in tri]);pos=np.array([v.co[:] for v in me.vertices]);uv=np.array([v.uv[:] for v in me.uv_layers['UVMap'].data]);n=np.array([v.vector[:] for v in me.corner_normals]);t=np.array([v.tangent[:] for v in me.loops]);sign=np.array([v.bitangent_sign for v in me.loops]);piece=np.array([v.value for v in me.attributes['piece'].data]);cf=[v.value for v in me.attributes['cuff'].data]
 keys=[]
 for f,ii in zip(tri,ids):
  pi=int(piece[ii[0]]);tag=cf[f.polygon_index] if pi==0 else 0;keys.append((pi,tag,int(pos[ii,0].mean()>0) if pi==0 and tag else 0))
 return dict(P=pos[ids],UV=uv[loops],N=n[loops],T=t[loops],S=sign[loops],keys=keys)
def posed_arrays(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 for face in body.data.polygons:face.use_smooth=True
 bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();obj=body.copy();obj.data=em.copy();obj.parent=None;obj.modifiers.clear();bpy.context.collection.objects.link(obj);ev.to_mesh_clear();return arrays(obj)
H=posed_arrays(out/'before/export/mm6_mnk1.blend');L=posed_arrays(p/'work/review4_rebaked.blend');trees={}

for key in set(H['keys']):
 ids=np.array([i for i,k in enumerate(H['keys']) if k==key]);verts=H['P'][ids].reshape(-1,3);trees[key]=(BVHTree.FromPolygons(verts.tolist(),np.arange(len(verts)).reshape(-1,3).tolist(),all_triangles=True),ids)
images={}
for name in ['basecolor_2k','region_mask','orm_1k','normal_1k']:
 im=bpy.data.images.load(str(out/f'before/textures/mnk1_{name}.png'),check_existing=False);im.colorspace_settings.name='Non-Color';a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);images[name]=a
images['basecolor_2k'][:,:,:3]=np.where(images['basecolor_2k'][:,:,:3]<=.04045,images['basecolor_2k'][:,:,:3]/12.92,((images['basecolor_2k'][:,:,:3]+.055)/1.055)**2.4)
images['normal_1k'][:,:,1]=1-images['normal_1k'][:,:,1]
result={name:np.zeros((size,size,4),np.uint8) for name in images};valid=np.zeros((size,size),bool);maxdist=0.;tested=0

def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-12)
def frame(data,ids,w):
 n=unit(np.einsum('ni,nij->nj',w,data['N'][ids]));t=np.einsum('ni,nij->nj',w,data['T'][ids]);t=unit(t-n*(t*n).sum(1,keepdims=True));s=np.sign((w*data['S'][ids]).sum(1));return n,t,np.cross(n,t)*s[:,None]
def sample(im,uv):
 h,w=im.shape[:2];q=uv*np.array([w,h])-.5;ij=np.floor(q).astype(int);f=q-ij;xx=ij[:,0]%w;yy=ij[:,1]%h;return (im[yy,xx]*(1-f[:,0,None])+im[yy,(xx+1)%w]*f[:,0,None])*(1-f[:,1,None])+(im[(yy+1)%h,xx]*(1-f[:,0,None])+im[(yy+1)%h,(xx+1)%w]*f[:,0,None])*f[:,1,None]
assert np.allclose(sample(np.array([[[1.,0,0,1],[0,1.,0,1]],[[0,0,1.,1],[1.,1,1,1]]]),np.array([[.25,.25],[.75,.75]])),[[1,0,0,1],[1,1,1,1]])
for i,(uv,P,key) in enumerate(zip(L['UV'],L['P'],L['keys'])):
 q=uv*size-.5;lo=np.maximum(np.ceil(q.min(0)).astype(int),0);hi=np.minimum(np.floor(q.max(0)).astype(int),size-1)
 if np.any(hi<lo):continue
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));xy=np.stack([x.ravel(),y.ravel()],1);A=(q[1:]-q[0]).T
 if abs(np.linalg.det(A))<1e-10:continue
 b=(xy-q[0])@np.linalg.inv(A).T;w=np.column_stack([1-b.sum(1),b]);keep=(w>=-1e-8).all(1);w=w[keep];xy=xy[keep]
 if not len(w):continue
 points=w@P;tree,globalids=trees[key];hits=[tree.find_nearest(Vector(v)) for v in points]
 # A thin hood has a black inner wall; nearest distance alone can select its back face.
 outward=unit(np.cross(P[1]-P[0],P[2]-P[0]));bad=np.where(np.array([h[1][:] for h in hits])@outward<.15)[0]
 for j in bad:
  options=[h for h in tree.find_nearest_range(Vector(points[j]),max(.02,hits[j][3]*2+.005)) if np.dot(h[1],outward)>.15]
  if options:hits[j]=min(options,key=lambda h:h[3])
 locations=np.array([h[0][:] for h in hits]);idx=globalids[np.array([h[2] for h in hits])];maxdist=max(maxdist,max(h[3] for h in hits));tested+=len(hits)
 hp=H['P'][idx];e=hp[:,1]-hp[:,0];f=hp[:,2]-hp[:,0];delta=locations-hp[:,0];ee=(e*e).sum(1);ff=(f*f).sum(1);ef=(e*f).sum(1);de=(delta*e).sum(1);df=(delta*f).sum(1);den=np.maximum(ee*ff-ef*ef,1e-20);u=(de*ff-df*ef)/den;v=(df*ee-de*ef)/den;hw=np.column_stack([1-u-v,u,v]);huv=np.einsum('ni,nij->nj',hw,H['UV'][idx]);hn,ht,hb=frame(H,idx,hw);ln,lt,lb=frame(L,np.full(len(w),i),w)
 xx,yy=xy.T;valid[yy,xx]=True
 for name,im in images.items():
  rgba=sample(im,huv)
  if name=='normal_1k':
   n=rgba[:,:3]*2-1;n=unit(ht*n[:,0,None]+hb*n[:,1,None]+hn*n[:,2,None]);rgba[:,:3]=(np.column_stack([(n*lt).sum(1),(n*lb).sum(1),(n*ln).sum(1)])+1)*.5
  if name=='basecolor_2k':rgba[:,:3]=np.where(rgba[:,:3]<=.0031308,rgba[:,:3]*12.92,1.055*np.clip(rgba[:,:3],0,None)**(1/2.4)-.055)
  if name=='region_mask':rgba[:,1:]=0
  result[name][yy,xx]=np.clip(rgba*255+.5,0,255).astype(np.uint8)
 if i%500==0:print('SURFACE_BAKE',i,len(L['P']),tested,flush=True)
assert tested>size*size*.1 and np.isfinite(maxdist)
np.savez_compressed(out/'surface_bake.npz',valid=valid,**result)
(out/'rebaked/bake.json').write_text(json.dumps(dict(method='Nearest actual triangle within the matching garment piece, barycentric source UV sampling; high MikkTSpace normal to low MikkTSpace normal. Supersampled then padded/downsampled.',samples=tested,atlas_size=size,occupied_fraction=float(valid.mean()),max_projection_distance_mm=maxdist*1000,source='review/round4/before/export/mm6_mnk1.blend',normal_convention='+Y up, matching accepted runtime',missed_samples=0),indent=2))
