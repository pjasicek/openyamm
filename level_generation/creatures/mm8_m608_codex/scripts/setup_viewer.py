"""Reuse the existing frame viewer; preview copies bake runtime ramps for Three.js only."""
from pathlib import Path
import sys,json,hashlib,re,copy,io
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';(V/'feedback').mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'claude_shared')]
from build_actor_lods import read_glb,write_glb
from region_variants import srgb_to_linear
for name in ['index.html','review.js']:
 s=(P.parent/'mm8_m596_claude/review/viewer'/name).read_text().replace('MM8 Crystal Walker','MM8 Juggernaut').replace('mm8_m596_claude','mm8_m608_codex').replace('mm6:cle','mm8:m608').replace('thief_','juggernaut_')
 if name=='index.html':
  s=re.sub(r'<header>.*?</header>','<header><h1>MM8 Juggernaut</h1><p>Three rigid rollers, heavy stone gestures and a crumble death. Native mint, blue and rose tiers.</p></header>',s,flags=re.S)
 else:s=re.sub(r'const focuses = .*?;',"const focuses = {body:[0,.53,0,2.6],head:[0,.9,.03,.65],arms:[0,.7,.02,1.9],shoulders:[0,.77,0,1.5],skirt:[0,.45,0,1.15],feet:[0,.20,0,1.4]};",s)
 (V/name).write_text(s)
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings": []}\n')
source=P/'export/mm8_m608.glb';original,raw=read_glb(source);source_hash=hashlib.sha256(source.read_bytes()).hexdigest();models=[]
def image(d,b,index):
 image=d['images'][d['textures'][index]['source']];v=d['bufferViews'][image['bufferView']];return Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]))
for variant,(tier,label) in enumerate(zip('abc',['Charger','Juggernaut','Demolisher'])):
 d=copy.deepcopy(original);b=bytearray(raw);used=set()
 for mesh in d['meshes']:
  for p in mesh['primitives']:
   for mapping in p.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
    if variant in mapping['variants']:p['material']=mapping['material']
   used.add(p['material'])
 cache={}
 for index in used:
  mat=d['materials'][index];ex=mat.get('extras',{});mask=ex.get('openyamm_region_mask');ramps=ex.get('openyamm_region_ramps')
  if not mask or not ramps:continue
  tex=mat['pbrMetallicRoughness']['baseColorTexture']['index'];key=(tex,mask['index'],json.dumps(ramps))
  if key not in cache:
   base=image(d,b,tex).convert('RGB');a=np.array(base,dtype=float)/255;linear=srgb_to_linear(a);lum=linear@np.array([.2126,.7152,.0722]);weights=np.array(image(d,b,mask['index']).convert('RGBA').resize(base.size,Image.Resampling.BILINEAR),dtype=float)/255
   for c,r in enumerate(ramps):
    t=np.clip((lum-r['range'][0])/(r['range'][1]-r['range'][0]),0,1)*15;lo=np.minimum(t.astype(int),14);f=t-lo;colors=np.array(r['colors']);target=colors[lo]*(1-f[...,None])+colors[lo+1]*f[...,None];w=weights[:,:,c,None];linear=linear*(1-w)+target*w
   srgb=np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055);out=io.BytesIO();Image.fromarray(np.round(np.clip(srgb,0,1)*255).astype('uint8')).save(out,format='PNG');payload=out.getvalue();b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload)});b.extend(payload);d['images'].append({'bufferView':len(d['bufferViews'])-1,'mimeType':'image/png'});d['textures'].append({'source':len(d['images'])-1,'sampler':0});cache[key]=len(d['textures'])-1
  mat['pbrMetallicRoughness']['baseColorTexture']['index']=cache[key]
 path=V/f'm608_{tier}_preview.glb';write_glb(path,d,b);sha=hashlib.sha256(path.read_bytes()).hexdigest();models.append({'id':tier,'label':label,'scale':1,'revision':'mm8_m608_v1','url':path.name+'?v='+sha[:10],'sha256':sha,'runtime_source_sha256':source_hash})
meta=json.loads((P/'work/animation_info.json').read_text());progress=json.loads((P/'creature_3d_progress.json').read_text());roles={'Standing':'standing','Walking':'walk','Attack':'attack','Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'};clips={}
for name,m in meta['clips'].items():
 native=progress['native_actions'][roles[name]];times=np.cumsum([0]+native['durations_ms'][:-1])/1000
 if name=='Attack':times=np.array([0,.25,.5,.85,1,1.065,1.125,1.25])
 anchors=[{'time':float(min(t,m['duration'])),'label':str(i+1),'phase':'Native source','source_images':['../../../mm8_packed_outline_collection_20261002/families/mm8_m608/native_variants/'+frame+'_609.png']} for i,(t,frame) in enumerate(zip(times,native['frames']))]
 clips[name]={'label':name,'duration':m['duration'],'mode':'loop' if m['loop'] else 'once','fps':48,'provenance':'Locally authored from native m608 poses. Walking rotates three rigid rollers; attack is timed to the native gameplay impact at 1.0 s; death breaks into 63 stones and the band.','anchors':anchors}
(V/'manifest.json').write_text(json.dumps({'revision':'mm8_m608_v1','model':models[0]['url'],'default_clip':'Standing','default_model':'a','feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2))
print('VIEWER_READY',V,flush=True)
