from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';info=json.loads((P/'export/export_info.json').read_text());models=[]
for tier,label in zip('abc',['Ghost · violet','Evil Spirit · blue','Specter · red']):
 f=V/f'mm6_gst_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'gst_{tier}','label':label,'url':f.name+'?v='+h[:12],'revision':'v3','sha256':h})
clips={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
 duration=info['clips'][name];prefix='atk' if name=='Attack' else 'wnc' if name=='Hit' else 'die' if name in ['Death','Dead'] else 'fly';letters='f' if name=='Dead' else 'abcdef';anchors=[]
 for i,letter in enumerate(letters):
  f=f'gst{prefix}{letter}0';anchors.append({'time':0 if name=='Dead' else duration*i/6,'label':f'Native {letter.upper()}','phase':'reference','source_images':[f'../../../mm6_gst/native/{f}.png']})
 clips[name]={'label':name,'duration':duration,'mode':'loop' if name in ['Standing','Walking','Running','Fidget'] else 'once','fps':60,'provenance':'Native floating motion and cross-front claw swipe; hit uses the owned GetHitF2 upper-body recoil.','anchors':anchors}
(V/'manifest.json').write_text(json.dumps({'revision':'v3','model':'MM6 Ghost','default_clip':'Standing','default_model':'gst_a','feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2)+'\n')
f=V/'index.html';f.write_text(f.read_text().replace('MM6 Ghost · animation WIP','MM6 Ghost · 3D review'))
