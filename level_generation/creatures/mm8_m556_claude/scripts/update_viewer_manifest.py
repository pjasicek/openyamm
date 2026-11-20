from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];v=P/'review/viewer';metrics=json.loads((P/'work/clip_metrics.json').read_text());manifest={'revision':'m556_slash_v2','model':'mm8_m556_a.glb','default_clip':'Attack','default_model':'wasp_a','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for c in 'abc':
 f=v/f'mm8_m556_{c}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();manifest['models'].append(dict(id='wasp_'+c,label='Wasp Warrior '+c.upper(),url=f.name+'?v='+sha[:12],revision='m556_slash_v2',sha256=sha))
for role,data in metrics.items():
 group={'Fly':'standing','FlyFast':'standing','Attack':'attack','Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'}[role];views=[0] if role in ['Death','Dead'] else range(5)
 manifest['clips'][role]=dict(label=role,duration=data['duration'],mode='loop' if role in ['Fly','FlyFast','Dead'] else 'once',provenance='Local insect rig; native source choreography and timings, coordinated wing/body motion.',anchors=[dict(time=0,label=role,phase='Native source study',source_images=[f'../../../mm7_mm8_packed_outline/session_mm8_05/mm8_m556/redo_2x/references/{group}_{i}_sheet_native.png' for i in views])])
 if role=='Attack':manifest['clips'][role]['impact']=.875
manifest['model_sha256']=manifest['models'][0]['sha256'];(v/'manifest.json').write_text(json.dumps(manifest,indent=2))
