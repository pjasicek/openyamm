"""Replace only recovery samples; retain accepted strike and unrelated binary payloads."""
import copy,json,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor
B=P/'work/review_round5_before';src=B/'export/mm6_natm.glb';old,original=read_glb(src);d=copy.deepcopy(old);b=bytearray(original)
s,sb=read_glb(P/'work/round5_animation.glb');sa=next(a for a in s['animations']if a['name']=='Attack');a=next(a for a in d['animations']if a['name']=='Attack');oa=copy.deepcopy(a);a['samplers']=[]
source={(s['nodes'][c['target']['node']]['name'],c['target']['path']):sa['samplers'][c['sampler']]for c in sa['channels']}
end=57;times=np.arange(end+1,dtype=np.float32)/48;ti=append_accessor(d,b,times[:,None],{'componentType':5126,'type':'SCALAR'},0);d['bufferViews'][-1].pop('target',None);d['accessors'][ti].update(min=[0.],max=[end/48])
for c in a['channels']:
 name=d['nodes'][c['target']['node']]['name'];path=c['target']['path'];ns=source[name,path];os=oa['samplers'][c['sampler']];ot=accessor_array(old,original,os['input']).ravel();ov=accessor_array(old,original,os['output']);nt=accessor_array(s,sb,ns['input']).ravel();nv=accessor_array(s,sb,ns['output'])
 values=np.column_stack([np.interp(times,nt,nv[:,i])for i in range(nv.shape[1])]).astype(np.float32)
 keep=46
 values[:keep]=np.column_stack([np.interp(times[:keep],ot,ov[:,i])for i in range(ov.shape[1])]).astype(np.float32)
 if path=='rotation':
  for i in range(1,len(values)):
   if values[i]@values[i-1]<0:values[i]*=-1
 idx=append_accessor(d,b,values,s['accessors'][ns['output']],0);d['bufferViews'][-1].pop('target',None);c['sampler']=len(a['samplers']);a['samplers'].append({'input':ti,'output':idx,'interpolation':'LINEAR'})
assert bytes(b[:len(original)])==bytes(original)
for key in ['meshes','skins','nodes','materials','images','textures']:assert d[key]==old[key]
assert [x for x in d['animations']if x['name']!='Attack']==[x for x in old['animations']if x['name']!='Attack']
write_glb(P/'export/mm6_natm.glb',d,b)
c=json.loads((B/'gates.json').read_text())
for prop in c['props']:
 for hand in prop.get('hands',[]):
  if hand.get('side')=='L'and 'intervals'in hand:hand['intervals']['Attack']=[[42/48,45/48]]
(P/'gates.json').write_text(json.dumps(c,indent=2)+'\n')
info=json.loads((B/'export/export_info.json').read_text());info['clips']['Attack']['duration']=end/48
(P/'export/export_info.json').write_text(json.dumps(info,indent=2)+'\n')
receipt={'old_duration_s':108/48,'new_duration_s':end/48,'removed_hold_frames':[46,52],'recovery_frames':[45,end],'recovery_intervals':12,'impact_s':.90625,'unchanged_binary_prefix_sha256':hashlib.sha256(original).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((P/'export/mm6_natm.glb').read_bytes()).hexdigest(),'unchanged':['geometry','skin weights','textures','materials','all eight other animations','both prop GLBs','strike through frame 45'],'method':'Cut hold; shared smooth world-space hand targets recover both arms with body from frame 45 to 57.'}
(P/'review/round5_retime.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
