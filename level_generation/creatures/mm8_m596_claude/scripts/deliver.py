"""Create the binding and reuse the shared creature viewer after the export gates pass."""
from pathlib import Path
import json
import hashlib
import shutil
import sys
import re
import numpy as np
import yaml

P=Path('level_generation/creatures/mm8_m596_claude')
sys.path.insert(0,'tools')
from build_actor_lods import read_glb,accessor_bytes
document,binary=read_glb(P/'export/mm8_m596.glb')
node=next(n for n in document['nodes'] if n.get('name')=='CrystalWalker')
primitive=document['meshes'][node['mesh']]['primitives'][0]
vertices=np.frombuffer(accessor_bytes(document,binary,primitive['attributes']['POSITION']),'<f4').reshape(-1,3)
height=float(np.ptp(vertices[:,1]));scale=191/height
audit=json.loads((P/'work/export_audit.json').read_text())
assert audit['geometry']['glb_sha256']==hashlib.sha256((P/'export/mm8_m596.glb').read_bytes()).hexdigest()
manifest=Path('assets_dev/worlds/mm8/models/actors.yml');manifest.parent.mkdir(parents=True,exist_ok=True)
data=yaml.safe_load(manifest.read_text()) if manifest.exists() else {'actors':[]}
data['actors']=[a for a in data['actors'] if a['descriptor'] not in {'Crystal Walker '+tier for tier in 'ABC'}]
for tier in 'ABC':
    binding={'descriptor':'Crystal Walker '+tier,'model':'worlds/mm8/models/mm8_m596.glb',
             'scale':round(scale*{'A':1,'B':1.299988,'C':1.599991}[tier],9),'yaw_offset':-1.570796327,
             'animation':{'cast':'Cast','run':'Running','stride_length':.90,'run_stride_length':1.30,
                          'upper_body_root':'Waist',
                          'sockets':{'palm_right':'RightHand','palm_left':'LeftHand'},
                          'events':{'attack_melee':{'impact':5/6},
                                    'attack_ranged':{'impact':5/6,'glow':['palm_right'],'release':'palm_right'},
                                    'cast':{'impact':5/6,'glow':['palm_left','palm_right']}},
                          'look':{'nodes':['Neck','Head'],'max_yaw_degrees':25,'max_pitch_degrees':15}},
             'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack',
                      'hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}}
    data['actors'].append(binding)
manifest.write_text(yaml.safe_dump(data,sort_keys=False))
(P/'work/scale.json').write_text(json.dumps({'native_height_px':191,'model_height_m':height,'scale':scale,
    'tier_frame_scales':[1,1.299988,1.599991],'same_palette':596},indent=2)+'\n')
viewer=P/'review/viewer';(viewer/'feedback').mkdir(parents=True,exist_ok=True)
template=Path('level_generation/creatures/mm6_rea_claude/review/viewer')
for name in ['index.html','review.js']:
    text=(template/name).read_text().replace('MM6 Sea Serpent','MM8 Crystal Walker').replace('MM6 Cleric','MM8 Crystal Walker').replace('mm6_cle_claude','mm8_m596_claude')
    if name=='index.html':
        text=re.sub(r'<header>.*?</header>','<header><h1>MM8 Crystal Walker</h1><p>Articulated crystal facets, native claw sweep and backward fall. Three native sizes share palette 596. Orbit, play, slow down or step through a pose.</p></header>',text,flags=re.S)
    else:
        text=text.replace('model=gltf.scene;model.animations=', 'model=gltf.scene;model.scale.setScalar(info.scale);model.animations=')
    (viewer/name).write_text(text)
if not (viewer/'feedback/user_feedback.json').exists():
    (viewer/'feedback/user_feedback.json').write_text('{"findings": []}\n')
sha=hashlib.sha256((P/'export/mm8_m596.glb').read_bytes()).hexdigest()
native={'Standing':'sa','Walking':'wa','Running':'wa','Attack':'aa','Cast':'aa','Hit':'na','Fidget':'fa','Death':'da','Dead':'xa'}
clips={k:{'label':k,'duration':v['duration'],'mode':'loop' if k in ['Standing','Walking','Running','Fidget','Dead'] else 'once',
          'provenance':'Authored rigid-part motion from original m596 frames; crystal facets never bend.',
          'anchors':[{'time':0,'label':k,'phase':'Native source',
                      'source_images':['../../../mm8_packed_outline_collection_20261002/families/mm8_m596/native_variants/m596'+native[k]+'0_596.png']}]}
       for k,v in json.loads((P/'work/build_report.json').read_text())['clips'].items()}
manifest={'revision':'mm8_m596_rigid_v1','model':'../../export/mm8_m596.glb','default_clip':'Standing','default_model':'a',
          'feedback':'feedback/user_feedback.json','models':[{'id':tier,'label':'Crystal '+label,'scale':factor,
          'revision':'mm8_m596_rigid_v1','url':'../../export/mm8_m596.glb?v='+sha[:12],'sha256':sha}
          for tier,label,factor in [('a','Walker (A)',1),('b','Sentry (B)',1.3),('c','Guardian (C)',1.6)]],'clips':clips}
(viewer/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
playback=Path('level_generation/creatures/mm8_m424_claude/scripts/viewer_playback.mjs').read_text()
playback=playback.replace("['Standing','Walking','Running','Hit','Death','Fidget','Dead']", "['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget','Dead']")
(P/'scripts/viewer_playback.mjs').write_text(playback)
print('Binding scale',scale,'viewer',viewer)
