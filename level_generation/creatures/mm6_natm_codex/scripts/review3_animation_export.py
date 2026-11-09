"""Transfer newly exported action samples onto the unchanged shared-atlas runtime geometry."""
import sys,copy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
path=P/'export/mm6_natm.glb';d,b=read_glb(path);s,sb=read_glb(P/'export/mm6_natm_raw_lod0.glb');names={n.get('name'):i for i,n in enumerate(d['nodes'])};mapping={}
for a in s['animations']:
 for ch in a['channels']:
  ni=ch['target']['node'];n=s['nodes'][ni];di=names[n['name']];dest=d['nodes'][di]
  for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert np.allclose(n.get(key,default),dest.get(key,default),atol=1e-6),(n['name'],key)
  mapping[ni]=di
accessors={};d['animations']=copy.deepcopy(s['animations'])
for a in d['animations']:
 for sampler in a['samplers']:
  for key in ['input','output']:
   idx=sampler[key]
   if idx not in accessors:
    accessors[idx]=append_accessor(d,b,accessor_array(s,sb,idx),s['accessors'][idx],0);d['bufferViews'][-1].pop('target',None)
    for extent in ['min','max']:
     if extent in s['accessors'][idx]:d['accessors'][-1][extent]=s['accessors'][idx][extent]
   sampler[key]=accessors[idx]
 for channel in a['channels']:channel['target']['node']=mapping[channel['target']['node']]
d,b=compact(d,b);write_glb(path,d,b)
