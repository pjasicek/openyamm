"""Append this family’s first-time binding from the audited export; refuse duplicates."""
from pathlib import Path
import json,hashlib,sys,yaml,numpy as np
P=Path('level_generation/creatures/mm8_m452_claude');sys.path.insert(0,'tools')
from build_actor_lods import read_glb,accessor_bytes
model=P/'export/mm8_m452.glb';sha=hashlib.sha256(model.read_bytes()).hexdigest()
audit=json.loads((P/'work/export_audit.json').read_text());assert audit['geometry']['glb_sha256']==sha
doc,blob=read_glb(model);node=next(n for n in doc['nodes'] if n.get('name')=='Rat')
prim=doc['meshes'][node['mesh']]['primitives'][0]
verts=np.frombuffer(accessor_bytes(doc,blob,prim['attributes']['POSITION']),'<f4').reshape(-1,3)
height=float(np.ptp(verts[:,1]));scale=71/height
path=Path('assets_dev/worlds/mm8/models/actors.yml');content=path.read_text();data=yaml.safe_load(content)
descriptors=['Wererat Rat Form Male '+tier for tier in 'ABC']
assert not any(a['descriptor'] in descriptors for a in data['actors']), 'Binding already exists; inspect before updating.'
entries=[]
for tier,factor in zip('ABC',[1,1.25,1.5]):
 entries.append({'descriptor':'Wererat Rat Form Male '+tier,'model':'worlds/mm8/models/mm8_m452.glb',
  'scale':round(scale*factor,9),'yaw_offset':-1.570796327,
  'animation':{'cast':'Attack','run':'Running','stride_length':.30,'run_stride_length':.43,
   'upper_body_root':'Spine2','sockets':{},'events':{'attack_melee':{'impact':.65}},
   'look':{'nodes':['Neck1','Head'],'max_yaw_degrees':22,'max_pitch_degrees':15}},
  'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack',
   'hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
# Append only this family, retaining concurrent creature bindings and their comments verbatim.
path.write_text(content.rstrip()+'\n'+yaml.safe_dump(entries,sort_keys=False))
(P/'work/scale.json').write_text(json.dumps({'native_height_px':71,'model_height_m':height,'scale':scale,
 'tier_frame_scales':[1,1.25,1.5],'shared_palette':452},indent=2)+'\n')
print('Binding scale',scale)
