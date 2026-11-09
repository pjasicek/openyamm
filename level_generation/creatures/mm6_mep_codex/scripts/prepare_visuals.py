import json,numpy as np
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parents[1];native=json.loads((p/'review/skin_luminance.json').read_text());report={}
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
for level in range(4):
 folder=p/f'textures/lod{level}';cfg=json.loads((folder/'ramps.json').read_text())
 for entry,prefix in zip(cfg['materials'],['mep','mep_head','mep_staff']):
  base=lin(np.asarray(Image.open(folder/f'{prefix}_basecolor.png').convert('RGB'),np.float32)/255);mask=np.asarray(Image.open(folder/entry['mask']).convert('RGBA'),np.float32)/255;lum=base@np.array([.2126,.7152,.0722])
  for variant in cfg['variants']:
   out=base.copy()
   for channel,reg in enumerate(entry['ramps'][variant]):
    lo,hi=reg['range'];t=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(t.astype(int),14);f=(t-i)[...,None];colors=np.array(reg['colors']);colour=colors[i]*(1-f)+colors[i+1]*f;out=out*(1-mask[...,channel:channel+1])+colour*mask[...,channel:channel+1]
   Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype(np.uint8)).save(folder/f'{prefix}_review_{variant[-1]}.png')
   if level==0 and prefix=='mep_head':
    skin=mask[:,:,3]>.98;values=(out@np.array([.2126,.7152,.0722]))[skin];n=native['head_'+variant[-1]];row={'linear_mean':float(values.mean()),'linear_p90':float(np.percentile(values,90)),'native_mean':n['native_skin_mean'],'native_p90':n['native_skin_p90'],'pixels':int(skin.sum())};row['not_darker']=row['linear_mean']>=row['native_mean'] and row['linear_p90']>=row['native_p90'];report[variant]=row
(p/'review/final_skin_luminance.json').write_text(json.dumps(report,indent=2));assert all(r['not_darker'] for r in report.values());print('FINAL_SKIN',report)
