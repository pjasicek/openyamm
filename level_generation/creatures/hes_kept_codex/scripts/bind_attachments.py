"""Use the exact runtime inverse bind matrices, as tools/split_attachment.py does."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
D,B=read_glb(P/'export/hes_kept_m_ragged.glb');skin=D['skins'][0];ib=accessor_array(D,B,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);names=[D['nodes'][i]['name'] for i in skin['joints']];report={}
for part in ('collar','pick','club','plate'):
 d,b=read_glb(P/'work/props_fitted_world'/f'{part}.glb');b=bytearray(b);M=ib[names.index('Kept_'+part.capitalize())];N=np.linalg.inv(M[:3,:3]).T;worst=0.
 for node in d['nodes']:assert not any(k in node for k in ('matrix','translation','rotation','scale')),node
 for mesh in d['meshes']:
  for prim in mesh['primitives']:
   for name in ('POSITION','NORMAL'):
    i=prim['attributes'][name];a=accessor_array(d,b,i);trans=(np.c_[a,np.ones(len(a))]@M.T)[:,:3] if name=='POSITION' else a@N.T
    if name=='NORMAL':trans/=np.maximum(np.linalg.norm(trans,axis=1,keepdims=True),1e-12)
    else:worst=max(worst,float(abs((np.c_[trans,np.ones(len(trans))]@np.linalg.inv(M).T)[:,:3]-a).max()))
    prim['attributes'][name]=append_accessor(d,b,trans.astype(np.float32),d['accessors'][i],34962)
 for key in ('images','textures','samplers'):d.setdefault(key,[])
 write_glb(P/'export'/f'hes_kept_{part}.glb',*compact(d,b));assert worst<1e-6;report[part]={'bone':'Kept_'+part.capitalize(),'bind_round_trip_error_m':worst}
(P/'review/attachment_bind_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('ATTACHMENT_BIND',report)
