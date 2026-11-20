"""Preserve the disconnected face surface with bounded spatial reduction, retaining UV corners."""
from pathlib import Path
import sys,json,numpy as np
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root/'tools'))
import build_actor_lods as glb
p=Path(__file__).resolve().parents[1];path=p/'export/mm8_m540_lods.glb'
d,b=glb.read_glb(path);b=bytearray(b)
def arr(i):
 a=d['accessors'][i];return np.frombuffer(glb.accessor_bytes(d,b,i),dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]).reshape(a['count'],-1).copy()
assert d['materials'][1]['name'].startswith('OgreMageHead')
base=d['meshes'][0];head=next(pr for pr in base['primitives'] if pr['material']==1);attrs=head['attributes'];pos=arr(attrs['POSITION']);tri=arr(head['indices']).reshape(-1,3);report=[]
for level,(mi,cell) in enumerate(zip(base['extras']['openyamm_lods'],(.004,.008,.016)),1):
 xyz=pos.copy();groups={}
 for i,v in enumerate(pos):
  key=tuple(np.floor(v/cell).astype(int)) if v[1]>1.40 else ('neck',i)
  groups.setdefault(key,[]).append(i)
 cluster=np.empty(len(pos),int)
 for g,ids in enumerate(groups.values()):xyz[ids]=pos[ids].mean(0);cluster[ids]=g
 ids=cluster[tri];keep=(ids[:,0]!=ids[:,1])&(ids[:,0]!=ids[:,2])&(ids[:,1]!=ids[:,2]);selected=tri[keep]
 # Retain distinct UV corners, but remove duplicate surfaces introduced by spatial welding.
 _,unique=np.unique(np.sort(cluster[selected],axis=1),axis=0,return_index=True);selected=selected[np.sort(unique)]
 used,indices=np.unique(selected,return_inverse=True);out={}
 for semantic,index in attrs.items():
  a=dict(d['accessors'][index]);a['count']=len(used);v=(xyz if semantic=='POSITION' else arr(index))[used]
  if 'min' in a:a['min']=v.min(0).tolist();a['max']=v.max(0).tolist()
  out[semantic]=glb.append_accessor(d,b,a,v.tobytes())
 index=glb.append_accessor(d,b,{'componentType':5125,'type':'SCALAR','count':indices.size},indices.astype('<u4').tobytes())
 mesh=d['meshes'][mi];slot=next(i for i,pr in enumerate(mesh['primitives']) if pr['material']==1)
 mesh['primitives'][slot]={'attributes':out,'indices':index,'material':1}
 delta=float(np.linalg.norm(xyz-pos,axis=1).max());assert delta<cell*1.74
 report.append({'level':level,'cell_m':cell,'head_triangles':len(selected),'max_vertex_displacement_m':delta})
for mi,shadow_index in zip([0]+base['extras']['openyamm_lods'],base['extras']['openyamm_shadow_lods']):
 d['meshes'][shadow_index]=glb.merge_shadow(d,b,d['meshes'][mi])
for mesh in d['meshes']:
 for primitive in mesh['primitives']:
  assert d['accessors'][primitive['indices']]['count']%3==0
glb.write_glb(path,d,b)
counts=[sum(d['accessors'][q['indices']]['count']//3 for q in d['meshes'][mi]['primitives']) for mi in [0]+base['extras']['openyamm_lods']]
assert all(a>b for a,b in zip(counts,counts[1:]))
manifest=json.loads((p/'export/lods.json').read_text());manifest['triangles']=counts
manifest['head_reduction']='Bounded spatial cells; see head_lods.json'
(p/'export/lods.json').write_text(json.dumps(manifest,indent=2)+'\n')
(p/'export/head_lods.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
