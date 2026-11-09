"""Retime exported input accessors exactly, preserving every pose and fractional release key."""
import sys,json,hashlib,copy
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
from merge_head_material import compact
rates={'Attack':1.5,'Cast':1.5,'Death':2.0}
for path in list((P/'export').glob('*.glb'))+list((P/'review/viewer').glob('*.glb')):
 if path.name=='mm6_lzd_lods.geometry.glb':continue
 d,b=read_glb(path);b=bytearray(b);changed=False
 for a in d.get('animations',[]):
  if a['name']not in rates:continue
  cache={};rate=rates[a['name']]
  for sampler in a['samplers']:
   old=sampler['input']
   if old not in cache:
    acc=copy.deepcopy(d['accessors'][old]);times=np.frombuffer(accessor_bytes(d,b,old),dtype='<f4').copy()/rate
    def ease(x):
     x=np.clip(x,0,1);return x*x*x*(10+x*(-15+6*x))
    if a['name']=='Death':
     times+=.10*(ease((times-.5)/.17)-ease((times-.5)/1.5))+.25*(ease((times-.95)/.50)-ease((times-.5)/1.5))
    else:times+=.012*(ease((times-.94)/.12)-ease((times-.7)/(.4333333333333333)))
    assert np.all(np.diff(times)>0)
    acc['min']=[float(times.min())];acc['max']=[float(times.max())]
    cache[old]=append_accessor(d,b,acc,times.tobytes())
   sampler['input']=cache[old]
  changed=True
 if changed:write_glb(path,*compact(d,b))
info=json.loads((P/'export/export_info.json').read_text())
for name,rate in rates.items():info['clips'][name]/=rate
info['impact_seconds']=.734375/1.5;(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
r=P/'integration/actors.yml';s=r.read_text().replace('Review round 4.','Review round 5.').replace('0.734375',format(info['impact_seconds'],'.12f'));r.write_text(s)
cfg=json.loads((P/'gates.json').read_text());cfg['props'][0]['hands'][0]['intervals']['Death']=[[0,.5]]
cfg['previous_counts']['body']['colour']=[9854,5141,2172,691];cfg['previous_counts']['bow']['colour']=[1788,964,388,110]
(P/'gates.json').write_text(json.dumps(cfg,indent=2))
receipt=json.loads((P/'review/round5/exports.json').read_text())
for name,x in receipt.items():
 path=P/f'export/{name}.glb';x.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
 d,b=read_glb(path)
 if name=='mm6_lzd':
  acts={a['name']:a for a in d['animations']}
  def channels(a):return {(c['target']['node'],c['target']['path']):tuple(accessor_bytes(d,b,a['samplers'][c['sampler']][k])for k in ['input','output'])for c in a['channels']}
  assert channels(acts['Attack'])==channels(acts['Cast'])
(P/'review/round5/exports.json').write_text(json.dumps(receipt,indent=2))
print('RETIMED',info['clips'],'release',info['impact_seconds'])

manifest=json.loads((P/'review/viewer/manifest.json').read_text());manifest['revision']='mm6_lzd_codex_round5'
for m in manifest['models']:
 path=P/'review/viewer'/('mm6_'+m['id']+'.glb');m['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();m['url']=path.name+'?v='+m['sha256'][:12];m['revision']=manifest['revision']
manifest['model_sha256']=manifest['models'][0]['sha256']
for name,c in manifest['clips'].items():
 c['duration']=info['clips'][name]
 c['provenance']=c['provenance'].replace('0.734375','0.489583333333')
 for anchor in c.get('anchors',[]):
  if anchor['time']>.48 and name in ['Attack','Cast']:anchor['time']=info['impact_seconds']
  anchor['phase']=anchor.get('phase','').replace('0.734375','0.489583333333')
(P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2))
