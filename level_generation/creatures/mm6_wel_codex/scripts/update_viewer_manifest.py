import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';audit=json.loads((P/'work/animation_audit.json').read_text());native=json.loads((P/'source/native_timing.json').read_text());clips={}
for name,info in audit.items():
 role={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Cast':'attack','Hit':'hit','Death':'death','Dead':'death','Fidget':'fidget'}[name];frames=native[role]['frames_front'];anchors=[{'time':i*info['duration']/max(1,len(frames)-1),'label':f,'phase':'native reference','source_images':['../../../mm6_wel/native/'+f+'.png']} for i,f in enumerate(frames)];clips[name]={'label':name,'duration':info['duration'],'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':'MM6 Water Elemental native choreography; local GetHitF2 recoil.','anchors':anchors}
clips['Attack']['provenance']='User-directed whole-body thrust: tail/hips load back, deeper draw, tip drives forward/inward toward the right-pectoral line; left arm counterbalances.'
clips['Attack']['anchors']=[{'time':t,'label':label,'phase':label,'source_images':[]} for t,label in [(0,'Ready'),(32/60,'Wind-up ends / immediate release'),(44/60,'Forward-inward impact'),(1.0,'Withdraw'),(79/60,'Ready')]]
models=[]
for tier,label in [('a','Water Beast'),('b','Water Spirit'),('c','Water Elemental')]:
 file=V/f'mm6_wel_{tier}.glb';sha=hashlib.sha256(file.read_bytes()).hexdigest();models.append({'id':'wel_'+tier,'label':label,'url':file.name+'?v='+sha[:12],'sha256':sha,'revision':'water_v6'})
(V/'manifest.json').write_text(json.dumps({'revision':'water_v6','model':'MM6 Water Elemental','default_clip':'Attack','default_model':'wel_a','feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2))
