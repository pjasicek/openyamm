"""One shared plated-knight atlas; native palette-index mapping supplies the three region-ramp tiers."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];T=P/'textures';M=P/'meshy/retexture_v1';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
N=1024;U=.90
load=lambda p,size=N:np.asarray(Image.open(p).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),float)/255
encode=lambda a:np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
raw=load(M/'texture_urls_0_base_color.png');ao=load(T/'knight_ao_1k.png')[...,0];raster=np.load(P/'work/uvraster_UVMap.npz');piece=raster['piece'];valid=piece>=0;nearest=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True);part=piece[tuple(nearest)]
base=raw*(.75+.25*ao[...,None]);base2=load(M/'texture_urls_0_base_color.png',2048)*( .75+.25*load(T/'knight_ao_1k.png',2048)[...,:1])
# Blue-violet painted inlays; saturated blue signal protects neutral metal highlights.
r,g,b=raw.transpose(2,0,1);accent=np.clip((b-g-.008)/.04,0,1)*np.clip(((b-g)/np.maximum(b,.01)-.045)/.13,0,1)
accent[np.isin(part,[15,16,21,22,19,20])]=np.maximum(accent[np.isin(part,[15,16,21,22,19,20])],.85)
accent=accent[tuple(nearest)];accent=ndimage.gaussian_filter(accent,.6);neutral=1-accent
classes=np.where(part==7,2,9).astype(np.uint8);normal=load(M/'texture_urls_0_normal.png');rough=load(M/'texture_urls_0_roughness.png')[...,0]
rough=np.where(part==7,.82,np.clip(rough,.32,.65));spec=np.where(part==7,.025,.9)*(.5+.5*ao);metal=load(M/'texture_urls_0_metallic.png')[...,0];mr=np.stack([spec,rough,metal],-1)
def squeeze(a):
 out=np.zeros_like(a);n=int(round(a.shape[1]*U));im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5));out[:,:n]=np.asarray(im.resize((n,a.shape[0]),Image.Resampling.LANCZOS),float)/255;return out
base=squeeze(base);base2=squeeze(base2);normal=squeeze(normal);mr=squeeze(mr);mask=np.stack([squeeze(np.repeat(accent[...,None],3,-1))[...,0],squeeze(np.repeat(neutral[...,None],3,-1))[...,0],np.zeros((N,N)),np.zeros((N,N))],-1)
classes=np.asarray(Image.fromarray(classes).resize((int(round(N*U)),N),Image.Resampling.NEAREST));cl=np.zeros((N,N),np.uint8);cl[:,:classes.shape[1]]=classes;classes=cl
swatches={};colours={'grip':(.28,.15,.065),'pommel':(.20,.22,.29),'guard':(.12,.14,.18),'blade':(.29,.31,.35),'edge':(.67,.70,.76)}
for j,(name,col) in enumerate(colours.items()):
 v=.10+j*.20;swatches[name]=[.95,v,.035]
 for arr in [base,base2]:
  n=arr.shape[0];y0,y1=int((1-v-.09)*n),int((1-v+.09)*n);x0,x1=int(.905*n),int(.995*n);yy,xx=np.mgrid[y0:y1,x0:x1];grain=.97+.03*np.sin(xx*.7+yy*.17);arr[y0:y1,x0:x1]=np.array(col)*grain[...,None]
 y0,y1=int((1-v-.09)*N),int((1-v+.09)*N);x0,x1=int(.905*N),int(.995*N);normal[y0:y1,x0:x1]=[.5,.5,1];mr[y0:y1,x0:x1]=[.05,.8,0] if name=='grip' else [.9,.32,.7];mask[y0:y1,x0:x1]=[0,0 if name=='grip' else 1,0,0];classes[y0:y1,x0:x1]=8 if name=='grip' else 9
# Exact native PNG colours reconstruct ACT indices without archived BMP access.
pals={k:np.frombuffer((ROOT/f'assets_dev/worlds/mm6/textures/pal{k}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k in [760,761,762]};counts=np.zeros(256)
tree=cKDTree(pals[760])
for f in (P.parent/'mm6_kni/native').glob('*.png'):
 a=np.asarray(Image.open(f).convert('RGBA'));rgb=a[a[:,:,3]>0,:3]/255;dist,ids=tree.query(rgb);assert dist.max()<.001;counts+=np.bincount(ids,minlength=256)
regions=[np.arange(87,199),np.r_[1:76,199:256]];variants=['kni_a','kni_b','kni_c'];ramps={v:[] for v in variants};reports=[];linbase=R.srgb_to_linear(base);lum=linbase@R.LUMA
for channel,ids in enumerate(regions):
 ids=ids[counts[ids]>0];native=R.srgb_to_linear(pals[760][ids])*1.35;ys=native@R.LUMA;targets={'kni_a':base}
 # Map native A brightness to the same entries in B/C; no cross-palette RGB ratios.
 order=np.argsort(ys);xs=ys[order];weights=np.sqrt(counts[ids][order]);q=np.linspace(0,1,256);curve_x=np.linspace(0,max(xs.max(),lum.max()),256)
 for v,k in zip(variants[1:],[761,762]):
  colors=R.srgb_to_linear(pals[k][ids][order])*1.35;curve=[]
  for x in curve_x:
   dd=(xs-x)**2;w=weights*np.exp(-(dd-dd.min())/.00015);curve.append(np.clip(w@colors/w.sum(),0,1))
  mapped=np.stack([np.interp(lum,curve_x,np.array(curve)[:,i]) for i in range(3)],-1);targets[v]=np.clip(encode(mapped),0,1)
 fitted,report=R.fit_ramps(base,targets,mask[...,channel],core_threshold=.8)
 for v in variants:ramps[v].append(fitted[v])
 reports.append(report)
for name,arr in [('knight_basecolor_2k.png',base2),('knight_normal_1k.png',normal),('knight_metal_rough_1k.png',mr),('knight_region_mask.png',mask)]:Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)).save(T/name)
Image.fromarray(classes).save(T/'knight_material_classes.png');(T/'sword_swatches.json').write_text(json.dumps(swatches,indent=2));(T/'knight_ramps.json').write_text(json.dumps({'variants':variants,'materials':[{'base':'KnightPlate_A','prefix':'KnightPlate','mask':'knight_region_mask.png','ramps':ramps}]},indent=2));(T/'palette_fit.json').write_text(json.dumps({'source_palettes':[760,761,762],'native_pixels':int(counts.sum()),'fit':reports,'materials':{'2':'hair','8':'grip leather','9':'plate armour and blade'},'mr_red':'specular mask; baked AO retained separately'},indent=2));print('TEXTURES',reports)
