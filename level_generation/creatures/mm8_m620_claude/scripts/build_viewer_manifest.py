from pathlib import Path
import json,struct,hashlib
p=Path(__file__).resolve().parents[1];v=p/'review/viewer'
b=(p/'export/mm8_m620_prepared.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];doc=json.loads(b[20:20+n]);roles={'Standing':('s','loop'),'Walking':('w','loop'),'Fidget':('f','loop'),'Hit':('n','once'),'Death':('d','once'),'Dead':('x','loop')};clips={}
for name,(source,mode) in roles.items():
 anim=next(x for x in doc['animations'] if x['name']==name);duration=max(doc['accessors'][s['input']]['max'][0] for s in anim['samplers']);frames=sorted((p/'source/native').glob(f'm620{source}*0.png'));anchors=[]
 for i,f in enumerate(frames):
  phase=i/max(1,len(frames)-1);files=[f'../../source/native/{f.stem[:-1]}{view}.png' for view in range(5)];assert all((v/x).exists() for x in files)
  anchors.append({'time':phase*duration,'label':str(i),'phase':phase,'source_images':files})
 clips[name]={'label':name,'duration':duration,'mode':mode,'provenance':'Accepted Male Peasant v2 civilian motion; fitted to the native Bedraggled Human build. Native poses are phase references.','anchors':anchors}
models=[]
for tier,color in [('a','green'),('b','blue'),('c','pale grey')]:
 f=v/f'mm8_bedraggled_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'bedraggled_{tier}','label':f'Tier {tier.upper()} · {color} vest','revision':'m620_solid_hair_v3','url':f.name+'?v='+h[:12],'sha256':h})
(v/'manifest.json').write_text(json.dumps({'revision':'m620_solid_hair_v3','default_model':'bedraggled_a','default_clip':'Standing','model':models[0]['url'],'model_sha256':models[0]['sha256'],'feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2)+'\n')
