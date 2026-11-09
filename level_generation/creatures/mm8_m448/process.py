"""Native-layout Wererat Ratman Form extraction, palette-aware edge repair and fixed tone."""
from pathlib import Path
import json,importlib.util,argparse,datetime
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
queue=module('queue',ROOT.parent/'mm8_restore_queue.py')
def save(p,d):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,indent=2)+'\n')
def edge_limits(name=None):
 if name is None:return json.loads((ROOT/'native_edge_audit.json').read_text())['family_maxima']
 return json.loads((ROOT/'native_frame_edge_limits.json').read_text())[name]
def spill(im,name=None):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];limits=edge_limits(name)
 band=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
 magenta=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-limits['magenta'])*alpha/255*band
 cyan=np.maximum(0,np.minimum(c[:,:,1],c[:,:,2])-c[:,:,0]-limits['cyan'])*alpha/255*band
 green=np.maximum(0,c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2])-limits['green'])*alpha/255*band
 score=np.maximum(np.maximum(magenta,cyan),green);y,x=np.unravel_index(np.argmax(score),score.shape)
 return {'max_score':float(score.max()),'max_magenta':float(magenta.max()),'max_cyan':float(cyan.max()),'max_green':float(green.max()),'candidates_above_12':int((score>12).sum()),'position':[int(x),int(y)],'native_allowances':limits,'band_px':4}
def fix(im,name=None):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];limits=edge_limits(name)
 band=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
 excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-limits['magenta'])*band
 c[:,:,0]-=excess;c[:,:,2]-=excess
 cyan=band&(c[:,:,1]>c[:,:,0]+limits['cyan'])&(c[:,:,2]>c[:,:,0]+limits['cyan'])
 c[:,:,2][cyan]=c[:,:,0][cyan]+limits['cyan']
 c[:,:,1][band]=np.minimum(c[:,:,1],np.maximum(c[:,:,0],c[:,:,2])+limits['green'])[band]
 a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8);a[alpha==0]=0
 return Image.fromarray(a)
def extract(im,name=None):
 if 'A' in im.getbands() and im.getchannel('A').getextrema()[0]<255:
  return fix(im.convert('RGBA'),name)
 c=np.array(im.convert('RGB'),float)/255;dom=np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1];core=dom<=max(20,edge_limits(name)['magenta']+5)/255;bg=(dom>210/255)&(c[:,:,0]>.9)&(c[:,:,2]>.9)&(c[:,:,1]<.1);dist,idx=ndi.distance_transform_edt(~core,return_indices=True);_,bi=ndi.distance_transform_edt(~bg,return_indices=True);f=c[idx[0],idx[1]];b=c[bi[0],bi[1]];v=f-b;alpha=np.clip(np.sum((c-b)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-8),0,1);alpha[core]=1;alpha[bg|(dist>7)]=0;rgb=(c-(1-alpha[:,:,None])*b)/np.maximum(alpha[:,:,None],1/255);rgb[core]=c[core];rgb[alpha==0]=0;out=Image.fromarray(np.dstack([np.round(np.clip(rgb,0,1)*255),np.round(alpha*255)]).astype(np.uint8));return fix(out,name)
def mean_luma(im):
 a=np.asarray(im).astype(float);weight=a[:,:,3]/255;return float(((a[:,:,:3]@np.array([.2126,.7152,.0722]))*weight).sum()/weight.sum())
