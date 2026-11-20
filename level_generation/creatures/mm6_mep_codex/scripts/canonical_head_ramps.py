import json,numpy as np
from PIL import Image
from pathlib import Path
p=Path(__file__).resolve().parents[1];T=p/'textures';cfg=json.loads((T/'mep_ramps.json').read_text());body,head=cfg['materials'][:2];assert body['base']=='Mep_A' and head['base']=='MepHead_A'
L=np.array([.2126,.7152,.0722]);lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);enc=lambda x:np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
base=lin(np.array(Image.open(T/'mep_head_basecolor_1k.png').convert('RGB'))/255);mask=np.array(Image.open(T/head['mask']))/255;old=base@L;new=old*(1-mask.sum(2));error=[]
def ramp(reg,luma):
 lo,hi=reg['range'];x=np.clip((luma-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);t=(x-i)[...,None];c=np.array(reg['colors']);return c[i]*(1-t)+c[i+1]*t
for c in range(4):
 wanted=ramp(head['ramps']['mep_a'][c],old);reg=body['ramps']['mep_a'][c];ys=np.array(reg['colors'])@L;xs=np.linspace(*reg['range'],16);assert np.all(np.diff(ys)>=-1e-6);mapped=np.interp(wanted@L,ys,xs);new+=mapped*mask[:,:,c];err=abs(ramp(reg,mapped)-wanted);core=mask[:,:,c]>.9
 if core.any():error.append({'region':c,'linear_rgb_mae':float(err[core].mean())})
base*=np.divide(new,np.maximum(old,1e-7))[...,None];base=np.clip(base,0,1);Image.fromarray(np.clip(enc(base)*255+.5,0,255).astype(np.uint8)).save(T/'mep_head_basecolor_1k.png');head['ramps']=body['ramps'];(T/'mep_ramps.json').write_text(json.dumps(cfg,indent=2));lum=base@L
for tier in 'abc':
 out=base.copy()
 for c,reg in enumerate(head['ramps']['mep_'+tier]):out=out*(1-mask[:,:,c:c+1])+ramp(reg,lum)*mask[:,:,c:c+1]
 Image.fromarray(np.clip(enc(out)*255+.5,0,255).astype(np.uint8)).save(T/f'mep_head_review_{tier}.png')
(p/'review/head_atlas_contract.json').write_text(json.dumps({'body_head_ramps_identical':True,'head_base_luminance_remapped_to_shared_ramps':True,'mean_errors':error},indent=2));print('HEAD_CANONICAL',error)
