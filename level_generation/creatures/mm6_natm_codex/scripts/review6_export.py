"""Replace the late pelvis/leg drive; retain unrelated binary payloads and the synchronized recovery."""
import copy,json,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor
B=P/'work/review_round6_before';src=B/'export/mm6_natm.glb';old,original=read_glb(src);d=copy.deepcopy(old);b=bytearray(original)
s,sb=read_glb(P/'work/round6_animation.glb');sa=next(a for a in s['animations']if a['name']=='Attack');a=next(a for a in d['animations']if a['name']=='Attack');oa=copy.deepcopy(a);a['samplers']=[]
source={(s['nodes'][c['target']['node']]['name'],c['target']['path']):sa['samplers'][c['sampler']]for c in sa['channels']}
end=55;times=np.arange(end+1,dtype=np.float32)/48;ti=append_accessor(d,b,times[:,None],{'componentType':5126,'type':'SCALAR'},0);d['bufferViews'][-1].pop('target',None);d['accessors'][ti].update(min=[0.],max=[end/48])
for c in a['channels']:
 name=d['nodes'][c['target']['node']]['name'];path=c['target']['path'];ns=source[name,path];os=oa['samplers'][c['sampler']];ot=accessor_array(old,original,os['input']).ravel();ov=accessor_array(old,original,os['output']);nt=accessor_array(s,sb,ns['input']).ravel();nv=accessor_array(s,sb,ns['output'])
 values=np.column_stack([np.interp(times,nt,nv[:,i])for i in range(nv.shape[1])]).astype(np.float32)
 source_times=(np.arange(end+1)+np.where(np.arange(end+1)>=43,2,0)).astype(np.float32)/48
 original_values=np.column_stack([np.interp(source_times,ot,ov[:,i])for i in range(ov.shape[1])]).astype(np.float32)
 affected=(name=='B_Pelvis'and path=='translation')or(name in [f'B_{side}_{part}'for side in 'LR'for part in ['Thigh','Calf','Foot']]and path=='rotation')
 if affected:original_values[33:43]=values[33:43]
 values=original_values
 if path=='rotation':
  for i in range(1,len(values)):
   if values[i]@values[i-1]<0:values[i]*=-1
 idx=append_accessor(d,b,values,s['accessors'][ns['output']],0);d['bufferViews'][-1].pop('target',None);c['sampler']=len(a['samplers']);a['samplers'].append({'input':ti,'output':idx,'interpolation':'LINEAR'})
assert bytes(b[:len(original)])==bytes(original)
for key in ['meshes','skins','nodes','materials','images','textures']:assert d[key]==old[key]
assert [x for x in d['animations']if x['name']!='Attack']==[x for x in old['animations']if x['name']!='Attack']
write_glb(P/'export/mm6_natm.glb',d,b)
print('EXPORTED',P/'export/mm6_natm.glb')

c=json.loads((B/'gates.json').read_text());c['props'][0]['impacts']['Attack']=35.5/48;c['props'][0]['hands'][1]['intervals']['Attack']=[[42/48,43/48]]
(P/'gates.json').write_text(json.dumps(c,indent=2)+'\n')
(P/'integration/actors.yml').write_text((B/'integration/actors.yml').read_text().replace('0.906250000','0.739583333'))
info=json.loads((B/'export/export_info.json').read_text());info['clips']['Attack']['duration']=55/48
(P/'export/export_info.json').write_text(json.dumps(info,indent=2)+'\n')
