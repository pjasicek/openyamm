from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';audit=json.loads((P/'work/clips.json').read_text());models=[]
for tier,label in zip('abc',['Flame Drake · green','Frost Drake · blue','Energy Drake · red']):
 f=V/f'mm6_drg1_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'drg1_{tier}','label':label,'url':f.name+'?v='+h[:12],'revision':'v9-scales','sha256':h})
clips={}
for name,info in audit.items():
 f={'Standing':'drg1hoa0','Walking':'drg1fla0','Running':'drg1fla0','Attack':'drg1ata0','Cast':'drg1ata0','Hit':'drg1wia0','Fidget':'drg1hoa0','Death':'drg1dea0','Dead':'drg1deh0'}[name];anchors=[{'time':0,'label':'Native','phase':'reference','source_images':[f'../../../mm6_drg1/native/{f}.png']}]
 clips[name]={'label':name,'duration':info['duration'],'mode':'loop' if name in ['Standing','Walking','Running'] else 'once','provenance':'Authored neck-and-jaw windup and breath release, informed by the native MM6 drake.' if name in ['Attack','Cast'] else 'Authored from MM6 Flying Drake sprite motion.','anchors':anchors}
for name in ['Death','Dead']:
 clips[name]['provenance']='Airborne burn-death motion; surface burning and fire are engine effects and are not shown in this viewer.'
d={'revision':'v9-scales','model':'MM6 Flying Drake','default_clip':'Standing','default_model':'drg1_a','feedback':'../feedback/user_feedback.json','models':models,'clips':clips};(V/'manifest.json').write_text(json.dumps(d,indent=2)+'\n')
