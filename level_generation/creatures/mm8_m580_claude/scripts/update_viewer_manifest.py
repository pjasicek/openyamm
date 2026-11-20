from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];v=P/'review/viewer';metrics=json.loads((P/'work/clip_metrics.json').read_text())
manifest={'revision':'m580_v1','model':'mm8_m580_a.glb','default_clip':'Swim','default_model':'turtle_a','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for c in 'abc':
 f=v/f'mm8_m580_{c}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();manifest['models'].append(dict(id='turtle_'+c,label='Dragon Turtle '+c.upper(),url=f.name+'?v='+sha[:12],revision='m580_v1',sha256=sha))
for role,data in metrics.items():
 group={'Swim':'walk','SwimIdle':'walk','Bite':'attack','Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'}[role]
 manifest['clips'][role]=dict(label=role,duration=data['duration'],mode='loop' if role in ['SwimIdle','Swim','Dead'] else 'once',provenance='Dedicated 18-bone turtle rig; native paddle, neck/bite and roll study. Rigid shell. Bite closes at the native damage time, 0.75 s.',anchors=[dict(time=0,label=role,phase='Native source study',source_images=[f'../../references/native_{group}.png'])])
 if role=='Bite':manifest['clips'][role]['impact']=.75
manifest['model_sha256']=manifest['models'][0]['sha256'];(v/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
