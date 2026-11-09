import json,hashlib,struct
from pathlib import Path
P=Path('level_generation/creatures/mm8_m632_claude');V=P/'review/viewer'
native=json.loads((P/'references_native/inventory.json').read_text())['bindings']['175']['actions']
roles={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Hit':'hit','Death':'death','Dead':'corpse','Fidget':'fidget'}
provenance={'Standing':'Authored upright breathing and low crossbow carry.','Walking':'Fitted two-hand crossbow walk, with native one-hand carry.','Running':'Fitted Mixamo Standard Run with native crossbow carry.','Attack':'Faster 0.90 s native raise, knee extension, weight shift and foot pivot into aim; two-hand approach at 2.5x over old frames 44–60, release at 1.05 s and recoil.','Hit':'Fitted front hit reaction with crossbow carry.','Death':'Fitted backward turn and fall; the crossbow releases outside the body.','Dead':'Exact final Death pose held.','Fidget':'Native left-hand chest/beard gesture.'}
r=(P/'export/mm8_m632_runtime_lod0.glb').read_bytes();d=json.loads(r[20:20+struct.unpack_from('<I',r,12)[0]])
durations={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
models=[]
for tier,label in zip('abc',('Grunt · green','Pounder · blue','Berserker · red')):
 name=f'mm8_m632_{tier}.glb';sha=hashlib.sha256((V/name).read_bytes()).hexdigest()
 models.append(dict(id=f'm632_{tier}',label=label,revision='m632_v5_fast_aim',url=name+'?v='+sha[:12],sha256=sha))
clips={}
for clip,role in roles.items():
 frames=native[role]['views']['0']; anchors=[]
 for i,f in enumerate(frames):
  t=durations[clip]*i/max(1,len(frames)-1)
  anchors.append(dict(time=t,label=f['frame'],phase=provenance[clip],source_images=[f"../../references_native/{f['frame']}.png"]))
 clips[clip]=dict(label=clip,duration=durations[clip],mode='loop' if clip in ('Standing','Walking','Running','Dead') else 'once',provenance=provenance[clip],anchors=anchors)
m=dict(revision='m632_v5_fast_aim',model=models[0]['url'],default_model='m632_a',default_clip='Standing',model_sha256=models[0]['sha256'],models=models,clips=clips,feedback='feedback/user_feedback.json')
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
