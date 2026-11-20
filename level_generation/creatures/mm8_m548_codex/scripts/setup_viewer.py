"""Reuse the existing viewer with this creature's scale, clips and native references."""
from pathlib import Path
import json,hashlib,re
P=Path(__file__).resolve().parents[1];out=P/'review/viewer';(out/'feedback').mkdir(parents=True,exist_ok=True)
for name in ['index.html','review.js']:
 s=(P.parent/'mm8_m596_claude/review/viewer'/name).read_text().replace('MM8 Crystal Walker','MM8 Crystal Dragon')
 if name=='index.html':
  s=re.sub(r'<header>.*?</header>','<header><h1>MM8 Crystal Dragon</h1><p>Wingless crystal quadruped: eight clips, three native sizes. Orbit, play or step through the movement.</p></header>',s,flags=re.S)
  s=s.replace('Arms / wrists','Front legs').replace('Shoulders / wings','Shoulders').replace('>Hands<','>Tail<').replace('Left palm faces backward during the sweep.','The front foot slides during the stride.')
 else:
  s=re.sub(r'const focuses = .*?;',"const focuses = {body:[0,.51,0,2.4], head:[0,.70,.38,.85], arms:[0,.22,.30,1.3], shoulders:[0,.4,.2,1.3], skirt:[0,.33,-.3,1.2], feet:[0,.06,0,1.4]};",s)
 (out/name).write_text(s)
feedback=out/'feedback/user_feedback.json'
if not feedback.exists():feedback.write_text('{"findings": []}\n')
sha=hashlib.sha256((P/'export/mm8_m548.glb').read_bytes()).hexdigest();revision='mm8_m548_v1'
meta=json.loads((P/'work/animation_info.json').read_text())
source=json.loads((P.parent/'mm8_m548/sources.json').read_text())['bindings']['112']['actions']
roles={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'}
clips={}
for clip,m in meta['clips'].items():
 frames=source[roles[clip]]['views']['0'];anchors=[]
 for i,f in enumerate(frames):
  stem=f['frame'][:-1];t=min(i*.125,m['duration'])
  anchors.append({'time':t,'label':str(i+1),'phase':'Native source','source_images':['../../../mm8_packed_outline_collection_20261002/families/mm8_m548/native_variants/'+stem+str(v)+'_548.png' for v in range(5)]})
 clips[clip]={'label':clip,'duration':m['duration'],'mode':'loop' if m['loop'] else 'once','provenance':'Authored quadruped motion from native m548 actions; continuous interpolation, native action timing. Running is an authored faster gait.','anchors':anchors}
manifest={'revision':revision,'model':'../../export/mm8_m548.glb','default_clip':'Standing','default_model':'a','feedback':'feedback/user_feedback.json','models':[{'id':tier,'label':label,'scale':scale,'revision':revision,'url':'../../export/mm8_m548.glb?v='+sha[:12],'sha256':sha} for tier,label,scale in [('a','Emerald Dragon (A)',1),('b','Sapphire Dragon (B)',1.199992),('c','Ruby Dragon (C)',2.199997/1.5)]],'clips':clips}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('VIEWER_READY',out)
