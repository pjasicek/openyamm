import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
audit=json.loads((P/'work/clips.json').read_text());clips={}
for name,info in audit.items():
 frames=['m492sa0']+[f'm492w{c}0' for c in 'abcdefghij']
 if name in ('Attack','Cast'):frames=[f'm492a{c}0' for c in 'abcdefghij']
 if name=='Hit':frames=['m492sa0']+[f'm492n{c}0' for c in 'abcdefghi']
 if name=='Death':frames=['m492sa0']+[f'm492d{c}0' for c in 'abcdefghij']
 if name=='Dead':frames=['m492xa0']
 anchors=[{'time':i*.125,'label':str(i),'phase':'native pose','source_images':[f'../../references/native/{f}.png']} for i,f in enumerate(frames)]
 clips[name]={'label':name,'duration':info['duration'],'mode':'once' if name in ('Attack','Cast','Hit','Death') else 'loop','provenance':'Authored native-informed six-limb flight; breath release at the native 1.25 second impact.','anchors':anchors}
h=hashlib.sha256((V/'mm8_m492.glb').read_bytes()).hexdigest()
manifest={'revision':'dragon-production-v1','model':'MM8 Dragon','default_clip':'Standing','default_model':'dragon','feedback':'../feedback/user_feedback.json','models':[{'id':'dragon','label':'Dragon · palette 492','url':'mm8_m492.glb?v='+h[:12],'sha256':h,'revision':'dragon-production-v1'}],'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
