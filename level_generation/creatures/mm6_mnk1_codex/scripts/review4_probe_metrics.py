import json,os,hashlib,shutil,numpy as np
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parents[1];out=p/'review/round4';tag=os.environ['TRIAL_TAG'];meta=json.loads((out/(tag+'_metadata.json')).read_text())[0];g=json.loads((out/(tag+'_gates_dense.json')).read_text());contacts=json.loads((out/(tag+'_g6_contacts.json')).read_text());pen=json.loads((out/(tag+'_penetration.json')).read_text());views={};dest=out/('probe_'+tag);dest.mkdir(exist_ok=True)
for i in range(8):
 a=np.array(Image.open(out/f'source_b_{i}.png'))[:,:,3]>127;b=np.array(Image.open(out/f'reduced_b_{i}_clay.png'))[:,:,3]>127;assert a.shape==b.shape==(800,800);views[str(i*45)]=float((a&b).sum()/(a|b).sum());shutil.copy2(out/f'reduced_b_{i}_clay.png',dest/f'{i}.png')
meta.update(sha256=hashlib.sha256((p/meta['path']).read_bytes()).hexdigest(),silhouette_iou=views,G4_max=max(v['stretch'][s+'_arm']['p99'] for v in g.values() for s in 'LR'),G5_max=max(v['stretch'][s+'_hand']['max'] for v in g.values() for s in 'LR'),contacts=contacts,penetration_pass=all(v['pass'] for v in pen['clips'].values()));meta['pass']=min(views.values())>=.99 and meta['G4_max']<=2 and meta['G5_max']<=4.5 and meta['penetration_pass'] and not any(contacts.values());(out/('probe_'+tag+'.json')).write_text(json.dumps(meta,indent=2));print('PROBE',meta['triangles'],min(views.values()),meta['pass'])
