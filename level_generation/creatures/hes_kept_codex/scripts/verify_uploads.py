"""Reimport real texture uploads; validate oriented triangles, normals, neutral materials and head UVs."""
import bpy,sys,os,json,struct,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];code='m' if kind=='male' else 'f'
data=np.load(P/'texturing'/f'kept_{code}_correspondence.npz');C=data['vertices'];F=data['faces'];head=data['head'];rows=[]
def signature(co,faces):
 co=[tuple(round(float(x),5)for x in p)for p in co];out=Counter()
 for f in faces:
  t=tuple(co[i]for i in f);out[min(t[k:]+t[:k]for k in range(3))]+=1
 return out
for what in ('body','head'):
 path=P/'texturing'/f'kept_{code}_{what}_upload.glb';raw=path.read_bytes();assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw));n,t=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);assert not g.get('skins') and not g.get('animations')
 assert len(g['meshes'])==1 and len(g['materials'])==1
 assert all('TEXCOORD_0' in p['attributes'] for m in g['meshes']for p in m['primitives'])
 for m in g['materials']:
  assert not m.get('doubleSided',False) and m.get('alphaMode','OPAQUE')=='OPAQUE'
  assert m['pbrMetallicRoughness'].get('metallicFactor',1)==0
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));objects=[o for o in bpy.data.objects if o.type=='MESH'];assert len(objects)==1
 ob=objects[0];me=ob.data;me.calc_loop_triangles();co=np.array([ob.matrix_world@v.co for v in me.vertices]);faces=np.array([t.vertices[:]for t in me.loop_triangles]);assert np.isfinite(co).all()
 expect=F[head] if what=='head' else F;assert signature(co,faces)==signature(C,expect),'Export changed oriented triangles'
 area=np.linalg.norm(np.cross(co[faces[:,1]]-co[faces[:,0]],co[faces[:,2]]-co[faces[:,0]]),axis=1)/2;assert area.min()>1e-10
 row={'upload':str(path.relative_to(P)),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':len(faces),'bytes':len(raw),'no_skins_or_animations':True,'single_sided_opaque':True,'oriented_triangles_preserved_at_10um':True,'min_triangle_area_m2':float(area.min()),'bounds_m':[co.min(0).tolist(),co.max(0).tolist()]}
 if what=='body':
  # Collapse reduction can move a sole by a fraction of a millimetre; posed soles have their separate floor gate.
  assert abs(co[:,2].min())<.002 and abs(np.ptp(co[:,2])-1.7)<.002
 else:
  uv=np.array([me.uv_layers.active.data[i].uv[:]for tri in me.loop_triangles for i in tri.loops]).reshape((-1,3,2));assert uv.min()>=-1e-6 and uv.max()<=1+1e-6
  # Pixel-centre occupancy excludes shared edges. Independent islands must not overlap.
  size=1024;occupancy=np.zeros((size,size),np.uint16)
  for t in uv:
   a,b,c=t*size;lo=np.maximum(np.floor(np.min(t*size,axis=0)).astype(int),0);hi=np.minimum(np.ceil(np.max(t*size,axis=0)).astype(int),size-1)
   if (hi<lo).any():continue
   xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);p=np.stack((xx,yy),-1)
   den=np.cross(b-a,c-a);assert abs(den)>1e-8
   v=np.cross(p-a,c-a)/den;w=np.cross(b-a,p-a)/den;inside=(v>1e-5)&(w>1e-5)&(v+w<1-1e-5)
   occupancy[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=inside
  overlap=int((occupancy>1).sum());assert overlap==0,overlap
  row.update(head_uv_bounds=[float(uv.min()),float(uv.max())],head_uv_overlap_pixels_1024=overlap,head_uv_coverage=float((occupancy>0).mean()))
 rows.append(row)
(P/'review'/kind/'texture_upload_validation.json').write_text(json.dumps({'pass':True,'uploads':rows},indent=2)+'\n');print('UPLOAD_VALIDATION',kind,rows,flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
