"""Restore the near body's measured skin luminance distribution after low-resolution rebaking."""
import sys,json,shutil,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1]
linear=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,12.92*c,1.055*np.maximum(c,0)**(1/2.4)-.055)
luma=np.array([.2126,.7152,.0722]);ref=P/'export/textures_lod0/body';im=np.asarray(Image.open(ref/'0_basecolor.png').convert('RGB'),float)/255;mask=np.asarray(Image.open(ref/'0_region_mask.png').convert('RGB'))[...,1]>.95*255;quantiles=np.linspace(0,1,1001);target=np.quantile(linear(im)[mask]@luma,quantiles);rows=[]
for level in [2,3]:
 folder=P/f'export/textures_lod{level}/body';path=folder/'0_basecolor.png';backup=folder/'0_basecolor_before_skin_calibration.png'
 if not backup.exists():shutil.copy2(path,backup)
 rgba=np.asarray(Image.open(backup).convert('RGBA'),float)/255;rgb=linear(rgba[:,:,:3]);lum=rgb@luma;mask=np.asarray(Image.open(folder/'0_region_mask.png').convert('RGB'),float)[...,1]/255;core=mask>.95;values=np.quantile(lum[core],quantiles);values,ids=np.unique(values,return_index=True);mapped=np.interp(lum,values,target[ids]);ratio=mapped/np.maximum(lum,1e-7);new=rgb*(1-mask[:,:,None])+rgb*ratio[:,:,None]*mask[:,:,None];rgba[:,:,:3]=np.clip(srgb(new),0,1);Image.fromarray(np.uint8(rgba*255+.5)).save(path);rows.append({'lod':level,'method':'Match linear skin luminance quantiles to the final LOD0 body, retaining chroma and alpha.'})
(P/'textures/far_skin_calibration.json').write_text(json.dumps(rows,indent=2))
