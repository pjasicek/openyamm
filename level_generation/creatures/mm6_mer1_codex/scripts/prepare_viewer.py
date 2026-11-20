"""Reuse the established review UI and bake the engine's linear region rule into portable tier GLBs."""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools'));import merge_head_material as G
V=P/'review/viewer';V.mkdir(exist_ok=True)
template=P.parent/'mm6_nobl_codex/review/viewer'
for name in ['index.html','review.js']:
 s=(template/name).read_text().replace('Swordsman, Expert and Master','Merchant A, B and C').replace('MM6 Swordsman','MM6 Merchant').replace('mm6-nobl-claude','mm6-mer1-codex').replace('Shoulders / cloak','Shoulders / sleeves').replace('mm6:nobl','mm6:mer1').replace('mm6_nobl_codex_frame_feedback','mm6_mer1_codex_frame_feedback').replace('barbarian_','merchant_')
 s=s.replace('body:[0,1.35,0,5.4], head:[0,1.78,0,1.4], arms:[0,1.2,0,2.8], shoulders:[0,1.85,0,3.4], skirt:[0,0.95,0,1.8], feet:[0,0.35,0,1.8]','body:[0,.85,0,3.7], head:[0,1.55,0,1.0], arms:[0,1.05,0,2.8], shoulders:[0,1.32,0,2], skirt:[0,.9,0,1.8], feet:[0,.15,0,1.8]')
 s=s.replace('Meshy preset. No native running animation and no claimed sprite-frame correspondence.','Owned-library running clip. Native mer1 has no separate running frames.')
 (V/name).write_text(s)
ramps=json.loads((P/'textures/mer1_ramps.json').read_text());selected=json.loads((P/'review/reduction/selection.json').read_text());folder=P/selected['body'][0]['textures'];entry=ramps['materials'][0]
rgb=np.asarray(Image.open(folder/'0_basecolor.png').convert('RGB'),float)/255;mask=np.asarray(Image.open(folder/'0_region_mask.png').convert('RGBA'),float)/255
lin=lambda x:np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
srgb=lambda x:np.where(x<=.0031308,x*12.92,1.055*np.clip(x,0,None)**(1/2.4)-.055)
base=lin(rgb);lum=base@np.array([.2126,.7152,.0722]);models=[]
for i,variant in enumerate(ramps['variants']):
 d,b=G.read_glb(P/'export/mm6_mer1_runtime_lod0.glb');out=base.copy()
 for c,reg in enumerate(entry['ramps'][variant]):
  lo,hi=reg['range'];colors=np.array(reg['colors']);t=np.clip((lum-lo)/(hi-lo),0,1)*15;k=np.minimum(t.astype(int),14);f=(t-k)[...,None];mapped=colors[k]*(1-f)+colors[k+1]*f;out=out*(1-mask[...,c:c+1])+mapped*mask[...,c:c+1]
 image=Image.fromarray(np.uint8(np.clip(srgb(out),0,1)*255+.5));image.save(V/f'{variant}_basecolor.png')
 mat=next(m for m in d['materials']if m['name']=='MerchantL0_A');mat['pbrMetallicRoughness']['baseColorTexture']={'index':G.add_image(d,b,image,variant,None)}
 d,b=G.compact(d,b);path=V/f'mm6_{variant}.glb';G.write_glb(path,d,b);digest=hashlib.sha256(path.read_bytes()).hexdigest()
 models.append({'id':variant,'label':['Merchant A — green','Merchant B — blue','Merchant C — red'][i],'revision':'mm6_mer1_codex_review1','url':path.name+'?v='+digest[:12],'sha256':digest})
clips={}
desc={'Standing':'Standard Idle (Mixamo), upright relaxed arms.','Walking':'ArmedWalk (owned humanoid set), upright stance and planted 0.84 m gait.','Running':'Jogging (Mixamo), upright arm swing with planted 1.302 m stride.','Attack':'Sword And Shield Slash (Mixamo), right-hand club draw, planted steps and follow-through.','Hit':'UnarmedGetHitF1 (owned humanoid set), delta around the relaxed standing pose.','Death':'Standing Death Forward 02 (Mixamo), forward fall, smoothed cloth; club remains hung from the belt.','Dead':'Held final Death pose.','Fidget':'Standing Idle 03 Examine (Mixamo), restrained to 18% around standing.'}
native=P.parent/'mm6_mer1/native'
def anchor(time,label,phase,stem):
 files=[f'../../../mm6_mer1/native/{stem}{i}.png'for i in range(5)if (native/f'{stem}{i}.png').exists()]
 return {'time':time,'label':label,'phase':phase,'source_images':files}
d,b=G.read_glb(V/'mm6_mer1_a.glb')
for a in d['animations']:
 role=a['name'];duration=max(float(G.accessor_array(d,b,s['input']).max())for s in a['samplers']);anchors=[]
 if role=='Standing':anchors=[anchor(0,'Standing','Native relaxed stance','mer1sta')]
 elif role=='Walking':anchors=[anchor(duration*i/6,chr(65+i),'Native walking phase (timing scaled to the planted gait)','mer1wa'+chr(97+i))for i in range(6)]
 elif role=='Attack':anchors=[anchor(t,l,'Native pose reference; library timing includes draw and recovery','mer1at'+chr(97+i))for i,(t,l)in enumerate(zip([0,.35,.65,.8125,1.1,1.5],'ABCDEF'))]
 elif role=='Death':anchors=[anchor(duration*i/5,chr(65+i),'Native fall pose reference; library fall has its own timing','mer1de'+chr(97+i))for i in range(6)]
 elif role=='Dead':anchors=[anchor(0,'Corpse','Native prone terminal pose','mer1def')]
 elif role=='Fidget':anchors=[anchor(0,'Standing','Native relaxed stance','mer1sta')]+[anchor(duration*(i+1)/5,chr(66+i),'Native fidget pose reference','mer1fi'+chr(98+i))for i in range(5)]
 elif role=='Hit':anchors=[anchor(duration*i/5,chr(65+i),'Native hit reaction','mer1wi'+chr(97+i))for i in range(6)]
 clips[role]={'label':role,'duration':duration,'mode':'loop'if role in ['Standing','Walking','Running','Fidget']else'once','provenance':desc[role],'anchors':anchors}
manifest={'revision':'mm6_mer1_codex_review1','model':models[0]['url'],'default_clip':'Standing','default_model':'mer1_a','model_sha256':models[0]['sha256'],'models':models,'clips':{k:clips[k]for k in desc},'feedback':'feedback/notes.json'}
(V/'feedback').mkdir(exist_ok=True);(V/'feedback/notes.json').write_text('{"findings":[]}\n');(V/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'tiers':len(models),'clips':len(clips),'models':models},indent=2))
