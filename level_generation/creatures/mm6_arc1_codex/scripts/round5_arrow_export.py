"""Smooth the zero-scale arrow's exported orientation without changing visible keyed poses."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array
p=P/'export/mm6_arc1.glb';before=hashlib.sha256(p.read_bytes()).hexdigest();d,b=read_glb(p);rows={}
def slerp(a,z,t):
 a=a.astype(float);z=z.astype(float)
 if a@z<0:z=-z
 dot=np.clip(a@z,-1,1)
 if dot>.9995:q=a*(1-t)+z*t
 else:
  angle=np.arccos(dot);q=(a*np.sin((1-t)*angle)+z*np.sin(t*angle))/np.sin(angle)
 return q/np.linalg.norm(q)
for a in d['animations']:
 if a['name']not in ['Attack','Cast']:continue
 samplers={c['target']['path']:a['samplers'][c['sampler']]for c in a['channels']if d['nodes'][c['target']['node']].get('name')=='Arrow'}
 r,s=samplers['rotation'],samplers['scale'];times=accessor_array(d,b,r['input']).ravel();st=accessor_array(d,b,s['input']).ravel();scale=accessor_array(d,b,s['output']);old=accessor_array(d,b,r['output']);q=old.copy()
 visible=np.max(np.stack([np.interp(times,st,scale[:,i])for i in range(3)],1),1)>1e-6
 first,last=np.flatnonzero(visible)[[0,-1]]
 for i in range(1,first):q[i]=slerp(old[0],old[first],(times[i]-times[0])/(times[first]-times[0]))
 for i in range(last+1,len(times)-1):q[i]=slerp(old[last],old[-1],(times[i]-times[last])/(times[-1]-times[last]))
 assert np.array_equal(q[visible],old[visible])and np.array_equal(q[[0,-1]],old[[0,-1]])
 acc=d['accessors'][r['output']];bv=d['bufferViews'][acc['bufferView']];offset=bv.get('byteOffset',0)+acc.get('byteOffset',0);stride=bv.get('byteStride',16)
 for i,v in enumerate(q):b[offset+i*stride:offset+i*stride+16]=v.astype('<f4').tobytes()
 rows[a['name']]={'changed_hidden_keys':int(np.any(old!=q,axis=1).sum()),'visible_keys_unchanged':int(visible.sum()),'rest_endpoints_unchanged':True}
write_glb(p,d,b);after=hashlib.sha256(p.read_bytes()).hexdigest()
(P/'review/round5/hidden_arrow_rotation.json').write_text(json.dumps({'before_sha256':before,'after_sha256':after,'clips':rows,'reason':'Zero-scale matrix decomposition replaces authored rotations with the rest frame. Smooth only the hidden keys toward/from the visible draw; retain visible keys and rest boundaries exactly.'},indent=2))
f=P/'review/round5/texture_sets.json';record=json.loads(f.read_text());asset=record['assets'][p.name];asset.setdefault('atlas_only_sha256',asset['sha256']);asset['sha256']=after;asset['bytes_after']=p.stat().st_size;asset['postprocess']='Hidden Arrow quaternion continuity; UVs/images unchanged';f.write_text(json.dumps(record,indent=2))
print('Hidden arrow continuity:',rows,after)
