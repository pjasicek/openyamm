from pathlib import Path
import json,sys,hashlib,shutil
import numpy as np
sys.path.insert(0,'tools');from merge_head_material import read_glb,accessor_array
p=Path(__file__).resolve().parents[1];out={}
for name in ['mm8_m444','mm8_m444_sword']:
 path=p/'export'/f'{name}.glb';d,b=read_glb(path);meshes=[]
 for mesh in d['meshes']:
  tris=0;weight_error=0;influences=0;uv_degenerate=0
  for primitive in mesh['primitives']:
   at=primitive['attributes'];pos=accessor_array(d,b,at['POSITION']);ind=accessor_array(d,b,primitive['indices']).ravel().reshape(-1,3);assert np.isfinite(pos).all() and ind.max()<len(pos);tris+=len(ind)
   uv=accessor_array(d,b,at['TEXCOORD_0']);assert np.isfinite(uv).all();q=uv[ind];areas=abs((q[:,1,0]-q[:,0,0])*(q[:,2,1]-q[:,0,1])-(q[:,1,1]-q[:,0,1])*(q[:,2,0]-q[:,0,0]));uv_degenerate+=int((areas<1e-12).sum())
   if 'WEIGHTS_0' in at:
    weights=np.concatenate([accessor_array(d,b,at[k]) for k in sorted(at) if k.startswith('WEIGHTS_')],1);weight_error=max(weight_error,float(np.max(abs(weights.sum(1)-1))));influences=max(influences,int((weights>1e-7).sum(1).max()));assert weight_error<.001 and influences<=8
  meshes.append({'name':mesh.get('name'),'triangles':tris,'max_weight_sum_error':weight_error,'max_influences':influences,'zero_area_uv_faces':uv_degenerate})
 assert all(a['triangles']>b['triangles'] for a,b in zip(meshes[:3],meshes[1:4]))
 out[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'meshes':meshes,'materials':len(d['materials']),'joints':len(d.get('skins',[{'joints':[]}])[0]['joints']),'animations':[a['name'] for a in d.get('animations',[])]}
(p/'work/final_asset_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
