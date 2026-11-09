"""Keep the knife LODs, shared detailed maps and tangent frames in the rigid attachment."""
import sys,copy,json,numpy as np
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
doc,data=read_glb(P/'work/tiers_combined.glb');out=copy.deepcopy(doc);buf=bytearray(data);skin=doc['skins'][0];slot=next(i for i,n in enumerate(skin['joints'])if doc['nodes'][n]['name']=='Knife');inv=accessor_array(doc,data,skin['inverseBindMatrices'])[slot].reshape(4,4).T
out['nodes']=[{'name':'Knife','mesh':0}];out['scenes']=[{'nodes':[0]}];out['scene']=0;out.pop('skins',None);out.pop('animations',None);out['meshes']=[]
for level in range(4):
 src=next(p for p in doc['meshes'][level]['primitives']if doc['materials'][p['material']]['name'].startswith('Knife'));attrs={}
 for name,index in src['attributes'].items():
  if name.startswith(('WEIGHTS_','JOINTS_')):continue
  a=doc['accessors'][index];v=accessor_array(doc,data,index).astype(np.float32)
  if name=='POSITION':v=(np.c_[v,np.ones(len(v))]@inv.T)[:,:3].astype(np.float32)
  if name in ['NORMAL','TANGENT']:
   xyz=v[:,:3]@inv[:3,:3].T;xyz/=np.maximum(np.linalg.norm(xyz,axis=1,keepdims=True),1e-10);v[:,:3]=xyz
  attrs[name]=append_accessor(out,buf,v,a,34962)
 prim=copy.deepcopy(src);prim['attributes']=attrs;out['meshes'].append({'name':'Knife'+(f'_LOD{level}'if level else''),'primitives':[prim]})
for m in out['meshes'][:4]:
 shadow=copy.deepcopy(m);shadow['name']+='_Shadow';out['meshes'].append(shadow)
out['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]}
write_glb(P/'export/mm6_mfp_knife.glb',*compact(out,buf))
print('KNIFE four levels, shared maps, tangents and shadows',flush=True)
