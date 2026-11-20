"""Recheck every contact touching a changed tile; retain hash-proven unchanged checks."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from check_land import checks
old=json.loads((HERE/'previous_delivery/complete_runtime_x2/manifest.json').read_text())
manifest_path=P/'complete_runtime_x2/manifest.json'
new=json.loads(manifest_path.read_text());folder=manifest_path.parent/'worlds/mm8/terrain_x2'
assert set(old['files'])==set(new['files'])
assert {n:sha(folder/n) for n in new['files']}=={n:r['sha256'] for n,r in new['files'].items()}
changed={n[:-4] for n in new['files'] if new['files'][n]['sha256']!=old['files'][n]['sha256']}
assert changed=={f.stem for f in (HERE/'runtime').glob('*.png')}
report=json.loads((HERE/'previous_delivery/reports/complete_validation.json').read_text())
assert not report['failures'] and report['manifest_sha256']==sha(HERE/'previous_delivery/complete_runtime_x2/manifest.json')
assert report['metric_source_sha256']==sha(P.parent/'mm7/check.py')
assert report['script_sha256']==sha(P/'check_complete_pack.py')
banks={r['name']:r for r in json.loads((P/'liquids/banks_v2/build.json').read_text())['tiles']}
cache={}
def tile(n,phase):
 key=(n,phase)
 if key not in cache:
  im=np.asarray(Image.open(folder/(n+'.png')),float)
  if im.shape[2]==4:
   prefix={'water':'hdwtr','lava':'hdlav','tar':'hwoil'}[banks[n]['binding']['liquid']]
   liquid=read(folder/('%s%03d.png'%(prefix,phase)));alpha=im[:,:,3:]/255
   im=im[:,:,:3]*alpha+liquid*(1-alpha)
  cache[key]=im
 return cache[key]
count=0
for r in report['checks']:
 if r['a'] in changed or r['b'] in changed:
  metric,_,_=checks.metrics(tile(r['a'],r['phase']),tile(r['b'],r['phase']),r['side']);r.update(metric);count+=1
report['failures']=[r for r in report['checks'] if not r['passed']]
report.update(manifest_sha256=sha(manifest_path),incremental_validation=dict(recomputed=count,reused=len(report['checks'])-count,previous_report_sha256=sha(HERE/'previous_delivery/reports/complete_validation.json'),script_sha256=sha(Path(__file__).resolve()),changed=sorted(changed)))
(P/'reports/complete_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Rechecked',count,'affected contacts;',len(report['failures']),'failures; unchanged checks reused with manifest hashes')
assert not report['failures']
