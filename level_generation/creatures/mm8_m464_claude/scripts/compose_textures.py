"""Padded PBR maps and native-palette cloth/hair ramps shared by all three peasants."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure

def load(label,suffix):return np.asarray(Image.open(P/f'meshy/{label}_retexture_v1/texture_urls_0_{suffix}.png').convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)

def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]

images={k:load(k,'base_color')for k in ['body','head']};data={k:np.load(P/f'work/uvraster_{k}.npz')for k in images};masks={}
for label,img in images.items():
 d=data[label];cov=d['piece']>=0;pos=d['pos'];h,s,v=np.moveaxis(np.asarray(Image.fromarray(np.uint8(img*255)).convert('HSV'),float)/255,-1,0)
 cloth=cov&(h>.20)&(h<.48)&(s>.15)&(pos[...,2]<1.45)
 hair=cov&(d['piece']==6) if label=='head' else np.zeros_like(cov)
 masks[label]=[cloth,hair]
# Use palette-index samples from all native standing angles; skin and metal stay unmasked.
sources=json.loads((P.parent/'mm8_m464/sources.json').read_text())['sources'];ids=np.concatenate([np.asarray(Image.open(P.parents[2]/v['path'])).ravel() for k,v in sources.items() if k.startswith('m464s')]);palettes={f'm464_{v}':i for v,i in zip('abc',[465,466,467])};ramps={k:[]for k in palettes};ranges=[]
for region,selection in enumerate([(ids>=23)&(ids<=116),(ids>=133)&(ids<=162)]):
 used=ids[selection];assert len(used)>100
 luminance=np.concatenate([R.luminance(images[label])[masks[label][region]] for label in images]);lo,hi=np.percentile(luminance,[.5,99.5]);ranges.append([float(lo),float(hi)])
 base=np.frombuffer((P.parents[2]/'assets_dev/worlds/mm8/textures/pal465.act').read_bytes()[:768],np.uint8).reshape(256,3)/255;order=np.argsort(R.luminance(base[used]));used=used[order]
 # Linear-luminance matching keeps the woven/painted shading while using the native palette colours.
 baseline=R.luminance(base[used]);b0,b1=np.percentile(baseline,[2,98]);target=np.linspace(b0,b1,16);sample=np.clip(np.searchsorted(baseline,target),0,len(used)-1)
 for name,index in palettes.items():
  pal=np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/pal{index}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255;colors=R.srgb_to_linear(pal[used[sample]]);ramps[name].append({'range':[float(lo),float(hi)],'colors':colors.tolist()})
report={}
for label,img in images.items():
 d=data[label];cov=d['piece']>=0;pos=d['pos'];cloth,hair=masks[label];h,s,v=np.moveaxis(np.asarray(Image.fromarray(np.uint8(img*255)).convert('HSV'),float)/255,-1,0)
 skin=cov&~cloth&~hair&(s>.12)&(h<.15)&(v>.30)&((pos[...,2]>.9)if label=='body'else True)
 leather=cov&(pos[...,2]<.48)&~cloth if label=='body'else np.zeros_like(cov)
 silver=cov&(s<.18)&(v>.45)&~skin&~hair;gold=leather&(h>.06)&(h<.18)&(s>.25)&(v>.25)
 normal=load(label,'normal');score=measure(np.uint8(normal*255+.5));assert score<-.15,(label,score);normal[...,1]=1-normal[...,1]
 rough=load(label,'roughness')[...,0];spec=np.full((N,N),.20);rg=np.clip(.84+.15*(rough-.5),.74,.94);metal=np.zeros((N,N));rg[skin]=.68;spec[skin]=.28;rg[hair]=.76;rg[leather]=.52;spec[leather]=.42;rg[silver|gold]=.46;spec[silver|gold]=.7;metal[silver|gold]=.6
 save(pad(img,cov),T/f'm464_{label}_basecolor.png');save(pad(normal,cov),T/f'm464_{label}_normal.png');save(np.stack([pad(spec,cov),pad(rg,cov),pad(metal,cov)],-1),T/f'm464_{label}_metal_rough.png')
 R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),cov),.5)for m in [cloth,hair]],T/f'm464_{label}_region_mask.png',size=N)
 overlay=img*.35;overlay[cloth]=(.1,1,.2);overlay[hair]=(1,.2,.1);save(overlay,P/'review'/f'{label}_regions.png');report[label]={'cloth_texels':int(cloth.sum()),'hair_texels':int(hair.sum()),'normal_integrability_before':score}
cfg={'variants':list(palettes),'palettes':palettes,'regions':['cloth','hair'],'report':report,'materials':[{'base':name+'_A','prefix':name,'mask':f'm464_{label}_region_mask.png','ramps':ramps}for label,name in [('body','VampirePeasant'),('head','VampirePeasantHead')]]};(T/'m464_ramps.json').write_text(json.dumps(cfg,indent=2));print('COMPOSE',report)
