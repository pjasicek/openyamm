"""Remove local painted costume remnants in object space while preserving anatomical detail elsewhere."""
import json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];old=P/'work/review_round4_before';L=np.array([.2126,.7152,.0722])
linear=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
base=np.array(json.loads((P/'review/round2_skin.json').read_text())['base_srgb_255'])/255;chroma=linear(base);chroma/=chroma@L
smooth=lambda v:np.clip(v,0,1)**2*(3-2*np.clip(v,0,1))
def selection(pos):
 x,y,z=pos.transpose(2,0,1);ax=abs(x)
 arm=smooth((ax-.165)/.02)*smooth((.355-ax)/.02)*smooth((z-1.12)/.025)*smooth((1.32-z)/.025)
 necklace=smooth((.115-ax)/.02)*smooth((z-1.255)/.025)*smooth((1.405-z)/.025)*smooth((-y-.10)/.025)
 streak=smooth((.045-ax)/.015)*smooth((z-1.20)/.02)*smooth((1.32-z)/.02)*smooth((-y-.10)/.025)
 return np.maximum.reduce([arm,necklace,streak])
r=np.load(P/'work/round2_raster_0_0.npz');pos=r['pos'];piece=r['piece'];valid=piece==0;alpha=selection(pos);source=np.array(Image.open(old/'export/textures_lod0/body/0_basecolor.png').convert('RGBA'),float)/255;lum=linear(source[...,:3])@L;donor=valid&(alpha<.001);points=pos[donor][::2];values=lum[donor][::2];tree=cKDTree(points);report={'method':__doc__,'deleted_fragment_piece':13,'normal_detail':'Unchanged on skin; neutralized only the two leather arm bands.','levels':{}}
for level in range(4):
 for mat in range(2):
  rel=Path(f'export/textures_lod{level}/body/{mat}_basecolor.png');rgba=np.array(Image.open(old/rel).convert('RGBA'),float)/255;r=np.load(P/f'work/round2_raster_{level}_{mat}.npz');piece=r['piece'];valid=piece>=0;_,near=distance_transform_edt(~valid,return_indices=True);piece=piece[tuple(near)];pos=r['pos'][tuple(near)];alpha=selection(pos)*(piece==0);sel=alpha>.001;rgb=linear(rgba[...,:3]);before=rgb.copy()
  dist,ids=tree.query(pos[sel],k=48,workers=4);weights=1/(dist+.008)**2;target=(values[ids]*weights).sum(1)/weights.sum(1);tone=chroma[None,:]*target[:,None];a=alpha[sel,None];rgb[sel]=rgb[sel]*(1-a)+tone*a
  bands=np.isin(piece,[12,15]);rgb[bands]=chroma*.028
  maskpath=P/rel.with_name(f'{mat}_region_mask.png');mask=np.array(Image.open(old/rel.with_name(f'{mat}_region_mask.png')));mask[(piece==0)|bands]=[0,255,0];Image.fromarray(mask).save(maskpath)
  rgba[...,:3]=srgb(rgb);Image.fromarray(np.uint8(np.clip(rgba,0,1)*255+.5)).save(P/rel)
  normal_rel=rel.with_name(f'{mat}_normal.png');normal=np.array(Image.open(old/normal_rel).convert('RGB'));normal[bands]=[128,128,255];Image.fromarray(normal).save(P/normal_rel)
  report['levels'][f'{level}/{mat}']={'skin_pixels_touched':int((sel&valid).sum()),'band_pixels':int((bands&valid).sum()),'outside_selection_max_delta':float(abs(rgb[(piece==0)&~sel]-before[(piece==0)&~sel]).max())if np.any((piece==0)&~sel)else 0}
(P/'review/round4_skin.json').write_text(json.dumps(report,indent=2));print('ROUND4_SKIN',report,flush=True)
