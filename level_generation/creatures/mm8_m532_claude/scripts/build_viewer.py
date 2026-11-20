from pathlib import Path
import sys,json,hashlib,copy,re
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];repo=P.parents[2];sys.path.insert(0,str(repo/'tools'));sys.path.insert(0,str(P.parent/'claude_shared'))
from merge_head_material import read_glb,write_glb,image_of,add_image
import tier_textures as T
import region_variants as R
V=P/'review/viewer';V.mkdir(exist_ok=True);(V/'feedback').mkdir(exist_ok=True)
original=P.parent/'mm6_natm_claude/review/viewer'
for name in ('index.html','review.js'):
    s=(original/name).read_text().replace('MM6 Sea Serpent','MM8 Centaur').replace('MM6 Cannibal','MM8 Centaur').replace('Cannibal','Centaur').replace('mm6-natm-claude','mm8-centaur-claude').replace('mm6_natm_claude_v1','mm8_centaur_v1')
    s=s.replace('body:[0,1.35,0,5.4], head:[0,1.78,0,1.4], arms:[0,1.2,0,2.8], shoulders:[0,1.85,0,3.4], skirt:[0,0.95,0,1.8], feet:[0,0.35,0,1.8]', 'body:[0,1.35,0,6.5], head:[0,2.32,.62,1.4], arms:[0,1.9,.75,2.8], shoulders:[0,2.0,.55,3.4], skirt:[.45,1.5,.85,1.4], feet:[0,.35,0,2.4]')
    if name=='index.html':
        s=re.sub(r'<header>.*?</header>', '<header><h1>MM8 Centaur · Centaur Warrior · Centaur Warlord</h1><p>Native palette tiers, animated bow and quiver. Nine actions on a fitted hybrid rig, including Shield casting.</p></header>',s,flags=re.S).replace('Shoulders / wings','Shoulders')
    s=s.replace('mm6:natm','mm8:m532').replace('mm6_natm_claude','mm8_m532_claude')
    (V/name).write_text(s)
(V/'feedback/user_feedback.json').write_text('{"findings": []}\n')
cfg=json.loads((P/'textures/centaur_ramps.json').read_text());models=[]
for tier in cfg['variants']:
    d,b=read_glb(P/'export/mm8_centaur_prepared.glb')
    for entry in cfg['materials']:
        m=next(m for m in d['materials']if m['name']==entry['base']);info=m['pbrMetallicRoughness']['baseColorTexture'];im,_=image_of(d,b,info['index']);base=np.asarray(im.convert('RGB'),float)/255
        mask=np.asarray(Image.open(P/'textures'/entry['mask']).convert('RGBA'),float)/255
        rgb=T.apply(base,mask,entry['ramps'][tier]);im=Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5));info['index']=add_image(d,b,im,entry['base']+'_'+tier,None)
    d,b=R._compact(d,b);file=V/(tier+'.glb');write_glb(file,d,bytearray(b));sha=hashlib.sha256(file.read_bytes()).hexdigest();models.append({'id':tier,'label':tier.replace('_',' ').title(),'revision':'mm8_centaur_v1','url':file.name+'?v='+sha[:12],'sha256':sha})
clips=json.loads((P/'work/clips.json').read_text());sources={'Standing':['sa'],'Walking':['wa','wb','wc','wd','we','wf'],'Running':['wa','wb','wc','wd','we','wf'],'Attack':['aa','ab','ac','ad','ae','af','ag','ah'],'Cast':['aa','ab','ac','ad','ae','af','ag','ah'],'Hit':['na','nb','nc','nd','ne','nf','ng'],'Death':['na','nb','da','db','dc','dd','df'],'Dead':['df'],'Fidget':['fa','fb','fc','fd']}
for name,info in clips.items():
    info.update(label=name,duration=info.pop('duration_seconds'),mode='loop'if name in ('Standing','Walking','Running','Dead')else'once',provenance='Local hybrid rig and native-led motion; attack release at 1.0 s, Shield cast uses the free right hand',anchors=[{'time':k*min(info['frames']/info.get('fps',24),1.)/len(sources[name]),'label':f,'phase':'Original MM8 source','source_images':['../../native/m532'+f+str(v)+'.png'for v in range(5)]}for k,f in enumerate(sources[name])])
manifest={'revision':'mm8_centaur_v1','model':models[0]['url'],'default_clip':'Standing','feedback':'feedback/user_feedback.json','default_model':'centaur_a','model_sha256':models[0]['sha256'],'models':models,'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('VIEWER',models)
