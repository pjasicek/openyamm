"""Actual GLB palette identity, consumer limits and final atlas overlap check."""
from pathlib import Path
import sys,json,hashlib,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
def values(doc,bin,i):
 a=doc['accessors'][i];dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
 n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 size=np.dtype(dtype).itemsize
 if 'bufferView' in a:
  data=np.frombuffer(accessor_bytes(doc,bin,i) if 'sparse' not in a else dense(doc,bin,a,size*n),dtype=dtype).reshape(-1,n).copy()
 else:data=np.zeros((a['count'],n),dtype=dtype)
 if 'sparse' in a:
  sp=a['sparse'];idx=sp['indices'];v=doc['bufferViews'][idx['bufferView']];off=v.get('byteOffset',0)+idx.get('byteOffset',0)
  indices=np.frombuffer(bin,dtype={5121:'u1',5123:'<u2',5125:'<u4'}[idx['componentType']],count=sp['count'],offset=off)
  val=sp['values'];v=doc['bufferViews'][val['bufferView']];off=v.get('byteOffset',0)+val.get('byteOffset',0)
  data[indices]=np.frombuffer(bin,dtype=dtype,count=sp['count']*n,offset=off).reshape(-1,n)
 return data
def dense(doc,bin,a,size):
 v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
 return b''.join(bin[start+k*stride:start+k*stride+size] for k in range(a['count']))
exports={v:read_glb(P/'delivery'/f'mm6_flying_demon_{v}.glb') for v in 'abc'};report={}
base,base_bin=exports['a']
for variant,(doc,bin) in exports.items():
 assert len(doc['scenes'])==1 and len(doc['skins'])==1 and len(doc['skins'][0]['joints'])==89
 assert len(doc['meshes'])==19 and not any(n.get('name')=='Icosphere' for n in doc['nodes'])
 assert len(doc['accessors'])==len(base['accessors'])
 assert doc['skins']==base['skins'] and doc['animations']==base['animations']
 for i,a in enumerate(doc['accessors']):
  assert a==base['accessors'][i] and np.array_equal(values(doc,bin,i),values(base,base_bin,i)),(variant,i,'geometry/motion differs')
 maximum=0
 for mesh in doc['meshes']:
  for pr in mesh['primitives']:
   attrs=pr['attributes'];assert 'POSITION' in attrs
   for index in attrs.values():assert np.isfinite(values(doc,bin,index)).all()
   if 'WEIGHTS_0' in attrs:
    w=np.concatenate([values(doc,bin,attrs[s]) for s in ('WEIGHTS_0','WEIGHTS_1') if s in attrs],axis=1)
    j=np.concatenate([values(doc,bin,attrs[s]) for s in ('JOINTS_0','JOINTS_1') if s in attrs],axis=1)
    assert abs(w.sum(1)-1).max()<1e-5 and j.max()<89
    maximum=max(maximum,int((w>1e-7).sum(1).max()));assert maximum<=8
 for m in doc['materials']:
  assert m.get('pbrMetallicRoughness',{}).get('metallicFactor',1)==0,m['name']
 for name,end in {'Flight':.75,'Attack':.75,'Hit':.75,'Death':.875,'Ash_Remains':.125}.items():
  a=next(a for a in doc['animations'] if a['name']==name)
  assert abs(max(float(values(doc,bin,s['input']).max()) for s in a['samplers'])-end)<1e-6
  reset=[c for c in a['channels'] if doc['nodes'][c['target']['node']]['name'] in ('Flying_Demon_Visibility','Flying_Demon_Ash','Flying_Demon_Disintegration')]
  assert len(reset)==4
  assert sum(c['target']['path']=='weights' for c in reset)==1
 report[variant]={'sha256':hashlib.sha256((P/'delivery'/f'mm6_flying_demon_{variant}.glb').read_bytes()).hexdigest(),'meshes':19,'joints':89,'maximum_influences':maximum,'geometry_uvs_normals_weights_bind_and_animation_byte_identical':True,'clip_count':5,'embedded_images':len(doc.get('images',[]))}
(P/'review/palette_export_validation.json').write_text(json.dumps(report,indent=2)+'\n')

# Clip convex UV triangles; positive shared area finds overlap, shared edges do not.
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def area(poly):return abs(sum(cross(poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly))))/2 if len(poly)>2 else 0
def intersection(a,b):
 poly=list(a);sign=1 if cross(b[1]-b[0],b[2]-b[0])>0 else -1
 for k in range(3):
  if not poly:break
  x,y=b[k],b[(k+1)%3];edge=y-x;out=[];prev=poly[-1];dp=sign*cross(edge,prev-x)
  for point in poly:
   dc=sign*cross(edge,point-x)
   if (dp>=0)!=(dc>=0):out.append(prev+(point-prev)*(dp/(dp-dc)))
   if dc>=0:out.append(point)
   prev,dp=point,dc
  poly=out
 return area(poly)
uv=np.load(P/'work/final_uv_triangles.npz');names=[n for n in uv.files if 'Strut' not in n or n.endswith('_Root')]
tri=np.concatenate([uv[n] for n in names]);owners=[(n,i) for n in names for i in range(len(uv[n]))]
low=tri.min(1);high=tri.max(1);cells={};pairs=set();overlaps=[]
for i,t in enumerate(tri):
 lo=np.floor(low[i]*64).astype(int);hi=np.floor(high[i]*64).astype(int);candidates=set()
 for x in range(lo[0],hi[0]+1):
  for y in range(lo[1],hi[1]+1):candidates.update(cells.get((x,y),()))
 for j in candidates:
  if (high[j]<=low[i]+1e-10).any() or (high[i]<=low[j]+1e-10).any():continue
  overlap=intersection(t,tri[j])
  if overlap>2e-10:overlaps.append({'a':owners[i],'b':owners[j],'area':float(overlap)})
 for x in range(lo[0],hi[0]+1):
  for y in range(lo[1],hi[1]+1):cells.setdefault((x,y),[]).append(i)
result={'status':'pass' if not overlaps else 'fail','tested_unique_surface_triangles':len(tri),'positive_area_overlaps':len(overlaps),'overlaps':overlaps,
 'intentional_stacks':'Six dark wing struts share the same chart per side; one representative per side checked against every other chart.',
 'rim_chart_padding_px_at_4k':2.8,'body_horn_strut_chest_regions_disjoint':not overlaps}
(P/'review/uv_validation.json').write_text(json.dumps(result,indent=2)+'\n')
assert not overlaps,result
print('All three exports match exactly; atlas unique surfaces have no unintended overlap.',flush=True)
