"""Reuse the batch viewer and bake only its preview colours with the runtime ramp rule."""
import sys,json,io,hashlib,shutil,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,image_of,add_image,compact
V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True);(V/'feedback').mkdir(exist_ok=True)
template=P.parent/'mm6_jak1_codex/review/viewer'
html=(template/'index.html').read_text().replace('MM6 Jackalman','MM6 PeasantM4').replace('Black-skinned jackal guardian, hooked staff and native blue/purple/red cloth tiers.','Cannibal, Head Hunter and Witch Doctor: warm-brown skin, feather mantle, spear and forearm buckler.').replace('Shoulders / wings','Shoulders / feather mantle').replace('>Hands</option>','>Hands / spear grip</option>')
(V/'index.html').write_text(html)
js=(template/'review.js').read_text().replace('MM6 Jackalman','MM6 PeasantM4').replace('mm6-jak1','mm6-natm').replace('mm6:jak1','mm6:natm').replace('mm6_jak1','mm6_natm')
js=js.replace("body:[0,1.0,0,4.3], head:[0,1.65,0,1.3], arms:[0,1.2,0,2.8], shoulders:[0,1.85,0,3.4], skirt:[0,0.95,0,1.8], feet:[0,0.35,0,1.8]","body:[0,0.86,0,3.6], head:[0,1.53,0,0.85], arms:[0,1.13,0,2.1], shoulders:[0,1.38,0,1.65], skirt:[0,0.9,0,1.7], feet:[0,0.19,0,1.2]")
(V/'review.js').write_text(js)
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
linear=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
models=[]
for level in range(4):
 for vi,(tier,label)in enumerate([('natm_a','Cannibal'),('natm_b','Head Hunter'),('natm_c','Witch Doctor')]):
  if level and vi!=1:continue
  doc,buf=read_glb(P/f'review/runtime/combined_lod{level}.glb');used=set()
  for mesh in doc['meshes']:
   for pr in mesh['primitives']:
    mappings=pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]);pr['material']=next(m['material']for m in mappings if vi in m['variants']);used.add(pr['material']);pr.pop('extensions',None)
  for index in used:
   mat=doc['materials'][index];baseinfo=mat['pbrMetallicRoughness']['baseColorTexture'];im,_=image_of(doc,buf,baseinfo['index']);rgba=np.asarray(im.convert('RGBA'),float)/255;rgb=linear(rgba[:,:,:3]);lum=rgb@np.array([.2126,.7152,.0722]);mask,_=image_of(doc,buf,mat['extras']['openyamm_region_mask']['index']);mask=np.asarray(mask.convert('RGBA'),float)/255;out=rgb.copy()
   for channel,reg in enumerate(mat['extras']['openyamm_region_ramps']):
    x=np.clip((lum-reg['range'][0])/(reg['range'][1]-reg['range'][0]),0,1)*15;i=np.minimum(x.astype(int),14);f=x-i;colors=np.array(reg['colors']);r=colors[i]*(1-f[:,:,None])+colors[i+1]*f[:,:,None];a=mask[:,:,channel:channel+1];out=out*(1-a)+r*a
   pixels=np.dstack([np.clip(srgb(out),0,1),rgba[:,:,3]]);image=Image.fromarray(np.uint8(pixels*255+.5));sampler=doc['textures'][baseinfo['index']].get('sampler');baseinfo['index']=add_image(doc,buf,image,mat['name']+'_review',sampler);mat['extras'].pop('openyamm_region_mask',None);mat['extras'].pop('openyamm_region_ramps',None)
  doc.pop('extensions',None);doc.pop('extensionsUsed',None);doc,buf=compact(doc,buf);path=V/f'mm6_{tier}.glb'if level==0 else P/f'review/runtime/lod{level}_{tier}.glb';write_glb(path,doc,buf);digest=hashlib.sha256(path.read_bytes()).hexdigest();model_entry=({'id':tier,'label':label,'revision':'mm6_natm_codex_review_round_4','url':path.name+'?v='+digest[:12],'sha256':digest})
  if level==0:models.append(model_entry)
info=json.loads((P/'export/export_info.json').read_text());provenance={
'Standing':'Local Mixamo Standard Idle, source-frame retarget with relaxed native carry.',
'Fidget':'Local Mixamo Standing Idle 02 Looking, planted feet and quiet arm, knee and cloth response.',
'Walking':'Local humanoid ArmedWalk, 8–12 cm swing clearance and distance-matched foot placement.',
'Running':'Local humanoid RelaxRunForward, low flight and the runtime 1.55× stride.',
'Attack':'Cached 2HandSpearAttack10 reference fitted to the native raised-knee wind-up and low two-handed forward thrust.',
'Cast':'Local humanoid ArmedCastLAttack1, distinct left-palm Fire Bolt gesture; spear remains in the right hand.',
'Hit':'Local humanoid UnarmedGetHitF1 with both arms, held equipment and knees responding.',
'Death':'Local Mixamo backward death reaction, retimed 2x faster with the same endpoint and floor contact.',
'Dead':'Exact held endpoint of the backward Death clip.'}
clips={}
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 row=info['clips'][role];anchors=[];prefix={'Standing':'st','Walking':'wa','Running':'wa','Attack':'at','Cast':'at','Hit':'wi','Death':'de','Dead':'de','Fidget':'fi'}[role];letters=['a']if role=='Standing'else['f']if role=='Dead'else list('abcdef')
 for j,letter in enumerate(letters):
  views=range(5)if role in ['Standing','Walking','Running']else[0];time=0 if len(letters)==1 else row['duration']*j/(len(letters)-1)
  names=[f'../../../mm6_natm/native/natm{prefix}{letter}{view}.png'for view in views];assert all((V/n).exists()for n in names),names
  anchors.append({'time':time,'label':role+' '+letter.upper(),'phase':'Native sequence at normalized phase; approximate pose correspondence.'+(' Running uses the native walk reference.'if role=='Running'else' Cast is a distinct library spell gesture shown beside the native attack.'if role=='Cast'else''),'source_images':names})
 clips[role]={'label':role,'duration':row['duration'],'mode':row['mode'],'provenance':provenance[role],'anchors':anchors}
manifest={'revision':'mm6_natm_codex_review_round_4','model':'mm6_natm_a.glb','default_clip':'Standing','default_model':'natm_a','feedback':'feedback/user_feedback.json','models':models,'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2));print('VIEWER_READY',len(models),'tiers',len(clips),'clips')
