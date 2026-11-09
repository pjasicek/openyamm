"""Match armour/prop steel to measured native armour pixels, shared identically by all tiers."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];T=P/'textures';L=np.array([.2126,.7152,.0722])
lin=lambda a:np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
enc=lambda a:np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
# Explicit front armour rectangles exclude cloth, shield and skin. Low-saturation mask excludes tier dyes.
rois={'helmet':[111,13,133,46],'shoulder_left':[71,49,112,66],'shoulder_right':[128,48,155,64],
      'bracer':[77,97,93,131],'greave_left':[87,195,107,244],'greave_right':[133,195,155,243]}
a=np.array(Image.open(P.parent/'mm6_figc/native_variants/figcsta0_212.png').convert('RGBA'),float)/255
hsv=np.array(Image.fromarray(np.uint8(a[:,:,:3]*255)).convert('HSV'),float)/255
roi=np.zeros(a.shape[:2],bool)
for x0,y0,x1,y1 in rois.values():roi[y0:y1,x0:x1]=True
roi&=(a[:,:,3]>.5)&(hsv[:,:,1]<.20)&(hsv[:,:,2]>.10)
native=lin(a[:,:,:3][roi])@L
Image.fromarray(np.uint8(roi)*255).save(P/'review/round2/native_steel_samples.png')
assert len(native)>1000
cfg=json.loads((T/'figc_ramps.json').read_text());report={'native_source':'../mm6_figc/native_variants/figcsta0_212.png','rois':rois,'sample_count':len(native),'space':'Rec.709 luminance after sRGB decoding; report sRGB luminance also','target_linear_multiplier':.50,'highlight_ceiling_linear':.15,'materials':{}}
def stats(vals):return {'linear_p10_p50_p90':np.percentile(vals,[10,50,90]).tolist(),'srgb_p10_p50_p90':enc(np.percentile(vals,[10,50,90])).tolist()}
report['native']=stats(native)
body_head=[]
for suffix,uv in [('', 'UVMap'),('_head','HeadUV')]:
 b=np.array(Image.open(T/f'figc{suffix}_basecolor_1k.png').convert('RGB'),float)/255
 mk=np.array(Image.open(T/f'figc{suffix}_region_mask.png').getchannel('B'))>242
 mk&=np.load(P/'work'/f'uvraster_{uv}.npz')['piece']>=0
 body_head.append((lin(b)@L)[mk])
body_head=np.concatenate(body_head)
for m in cfg['materials']:
 suffix={'FighterChain_A':'','FighterChainHead_A':'_head','FighterChainGear_A':'_gear'}[m['base']];size='2k' if suffix=='_gear' else '1k'
 base=np.array(Image.open(T/f'figc{suffix}_basecolor_{size}.png').convert('RGB'),float)/255
 mask=np.array(Image.open(T/m['mask']).getchannel('B'),float)/255;core=mask>.95
 if suffix!='_gear':
  raster=np.load(P/'work'/('uvraster_HeadUV.npz' if suffix else 'uvraster_UVMap.npz'));core&=raster['piece']>=0
 else:
  # Restrict the generated reference to actual visible iron, avoiding its grey background.
  support=Image.new('L',(2048,2048));dr=ImageDraw.Draw(support)
  dr.polygon([(342,28),(678,28),(841,411),(696,1413),(654,1477),(372,1477),(328,1413),(178,411)],fill=255)
  dr.rectangle((1024+410,150,1024+610,486),fill=255)
  for mirror in [-1,1]:
   dr.polygon([(1024+512+mirror*x,y) for x,y in [(90,210),(210,175),(285,30),(410,300),(285,587),(210,421),(90,402)]],fill=255)
  core&=np.array(support)>0
 vals=lin(base)@L;values=vals[core];fit_values=values if suffix=='_gear' else body_head;lo,hi=np.percentile(fit_values,[.5,99.5]);stops=[]
 # Histogram-based mapping preserves the painted wear while matching the native grey distribution.
 for j in range(16):
  q=np.clip(np.mean(fit_values<=lo+(hi-lo)*j/15),.015,.985);v=min(.15,float(np.quantile(native,q))*.50);stops.append([v*.985,v,v*1.008])
 reg={'range':[float(lo),float(hi)],'colors':stops}
 for tier in cfg['variants']:m['ramps'][tier][2]=reg
 x=np.clip((values-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);f=x-i;out=np.array(stops)@L;result=out[i]*(1-f)+out[i+1]*f
 report['materials'][m['base']]={'base':stats(values),'mapped':stats(result),'range':[float(lo),float(hi)],'core_texels':int(core.sum())}
 assert np.median(result)<np.median(native)*.90,(m['base'],np.median(result),np.median(native))
 if suffix!='_gear':
  mr=np.array(Image.open(T/f'figc{suffix}_metal_rough_1k.png'));mr[mask>.5,0]=71;mr[mask>.5,1]=184;Image.fromarray(mr).save(T/f'figc{suffix}_metal_rough_1k.png')
(T/'figc_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(P/'review/round2/steel_luminance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
