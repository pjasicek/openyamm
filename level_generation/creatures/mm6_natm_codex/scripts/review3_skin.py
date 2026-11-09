"""Restore anatomical luminance/normal detail while removing hue patches and pink arm bands."""
import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];old=P/'work/review_round2_before';L=np.array([.2126,.7152,.0722])
linear=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
base=np.array(json.loads((P/'review/round2_skin.json').read_text())['base_srgb_255'])/255;chroma=linear(base);chroma/=chroma@L
report={'method':__doc__,'body_normal_strength':1,'skin_hue':'Round 2 native warm brown, unchanged','regions':{},'removed_pink_components':[12,15]}
for level in range(4):
 for mat in range(2):
  rel=Path(f'export/textures_lod{level}/body/{mat}_basecolor.png');before=P/'work/review_round3_before'/rel;before.parent.mkdir(parents=True,exist_ok=True)
  if not before.exists():shutil.copy2(P/rel,before)
  raster=np.load(P/f'work/round2_raster_{level}_{mat}.npz');piece,pos=raster['piece'],raster['pos'];valid=piece>=0;_,near=distance_transform_edt(~valid,return_indices=True);p=piece[tuple(near)];pos=pos[tuple(near)];x,y,z=pos.transpose(2,0,1);skin=p==0;bands=np.isin(p,[12,15])
  rgba=np.array(Image.open(old/rel).convert('RGBA'),float)/255;lum=rgba[...,:3]@L
  # Broad exposure balancing is continuous in 3D, so no UV-island boundaries are introduced.
  regions={'head':skin&(z>1.52),'neck':skin&(z>1.40)&(z<1.50),'chest':skin&(z>1.20)&(z<1.38)&(abs(x)<.17)&(y<-.07),'arms':skin&(abs(x)>.23)&(z>1.05)}
  chest=np.median(lum[regions['chest']&valid])if np.any(regions['chest']&valid)else .28
  neck=np.median(lum[regions['neck']&valid])if np.any(regions['neck']&valid)else chest
  head=np.median(lum[regions['head']&valid])if np.any(regions['head']&valid)else neck
  exposure=np.interp(z,[0,1.36,1.445,1.53,2],[chest,chest,neck,head,head])
  # Retain broad muscle relief and fine pores, compressing the earlier painted extremes.
  detail=np.clip((lum/np.maximum(exposure,.05))**.8,.45,1.75)
  neckblend=np.clip((z-1.33)/.065,0,1)*np.clip((1.55-z)/.07,0,1);detail=1+(detail-1)*(1-neckblend*.85)
  corrected=srgb(chroma[None,None,:]*(.052*detail**1.6)[...,None]);rgba[...,:3][skin]=corrected[skin]
  banddetail=np.clip(lum/np.maximum(np.median(lum[bands&valid])if np.any(bands&valid)else .3,.05),.65,1.25)
  rgba[...,:3][bands]=srgb(chroma[None,None,:]*(.035*banddetail)[...,None])[bands]
  Image.fromarray(np.uint8(np.clip(rgba,0,1)*255+.5)).save(P/rel)
  normal=rel.with_name(f'{mat}_normal.png');shutil.copy2(old/normal,P/normal)
  # Bands must use the skin palette as well as the shared brown albedo in every tier.
  maskpath=P/rel.with_name(f'{mat}_region_mask.png');mask=np.array(Image.open(maskpath));mask[bands]=[0,255,0];Image.fromarray(mask).save(maskpath)
  if level==0:
   for name,sel in regions.items():
    c=rgba[...,:3][sel&valid]
    if len(c):report['regions'][f'{mat}_{name}']={'mean_luminance_255':float((c@L).mean()*255),'p05_p50_p95':(np.percentile(c@L,[5,50,95])*255).tolist()}
  print('SKIN',level,mat,flush=True)
(P/'review/round3_skin.json').write_text(json.dumps(report,indent=2))
