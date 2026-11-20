"""Finalize float32 clip endpoints and prepare the shared runner's explicit whole-body floor probe."""
import sys,json,copy,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array
file=P/'export/mm6_natm.glb';doc,buf=read_glb(file);seen=set();changes=[]
for animation in doc['animations']:
 for sampler in animation['samplers']:
  i=sampler['input']
  if i in seen:continue
  seen.add(i);ac=doc['accessors'][i];times=accessor_array(doc,buf,i).reshape(-1);end=float(times[-1]);exact=round(end*48)/48
  if end>exact:
   times[-1]=np.nextafter(np.float32(exact),np.float32(-np.inf));view=doc['bufferViews'][ac['bufferView']];offset=view.get('byteOffset',0)+ac.get('byteOffset',0);buf[offset:offset+times.nbytes]=times.tobytes();ac['max']=[float(times[-1])];changes.append({'clip':animation['name'],'before':end,'after':float(times[-1])})
write_glb(file,doc,buf);(P/'review/round1_timing.json').write_text(json.dumps(changes,indent=2))
info=json.loads((P/'export/export_info.json').read_text());info['bones']=len(doc['skins'][0]['joints'])
for animation in doc['animations']:info['clips'][animation['name']]['duration']=max(doc['accessors'][s['input']]['max'][0]for s in animation['samplers'])
for row in info['lods']:row['textures']='export/textures_shared'
(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
# Sole-only defaults cannot see a mantle. The same shared evaluator checks all vertices during Death/Dead.
probe=copy.deepcopy(doc);probe['animations']=[a for a in probe['animations']if a['name']in ['Death','Dead']];write_glb(P/'review/round1_floor.glb',probe,buf)
config=json.loads((P/'gates.json').read_text());config['clips']={'rest':[],'walk':[],'run':[],'attack':[]};config['sole_band_m']=4
for side in 'LR':config['regions']['foot_'+side]={'bounds':[[-10,-10,-10],[10,10,10]]}
for prop in config['props']:prop['file']='../'+prop['file']
(P/'review/round1_floor.gates.json').write_text(json.dumps(config,indent=2))
(P/'review/round1_floor_provenance.json').write_text(json.dumps({'source':'export/mm6_natm.glb','source_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256((P/'review/round1_floor.glb').read_bytes()).hexdigest(),'changes':'Animation inventory narrowed to Death and Dead only. Geometry, skin, poses and materials unchanged. Both foot regions select the entire body, including feathers; a 4 m sole band includes every vertex. Rest/gait classification disabled for this corpse floor probe.'},indent=2))
print('FINALIZED',info['bones'],'bones; endpoint corrections',len(changes))
