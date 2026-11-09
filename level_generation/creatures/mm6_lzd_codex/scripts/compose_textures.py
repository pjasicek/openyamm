"""One padded cloth region; native 767/766/768 palette curves; shared matte skin and dull armor."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'));sys.dont_write_bytecode=True
from region_variants import fit_ramps,write_mask
T=P/'textures';T.mkdir(exist_ok=True)
def load(job,name):return np.array(Image.open(P/'meshy'/job/name).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS))/255
rep={}
for tag,job,layer in [('body','body_retexture_v1','UVMap'),('head','head_geometry_v1','HeadUV')]:
 r=np.load(P/f'work/uvraster_{layer}.npz');piece=r['piece'];valid=piece>=0;_,ix=distance_transform_edt(~valid,return_indices=True);pid=piece[ix[0],ix[1]]
 base=load(job,'texture_urls_0_base_color.png');normal=load(job,'texture_urls_0_normal.png');metal=load(job,'texture_urls_0_metallic.png')[:,:,0];rough=load(job,'texture_urls_0_roughness.png')[:,:,0]
 steel=np.isin(pid,[13,14,16,17,21,22]);skin=np.isin(pid,[1,3,4,200]);cloth=np.isin(pid,[2,12,15]) if tag=='body' else np.zeros_like(valid)
 base*=.90 if tag=='head' else .84;base[steel]*=.72
 if tag=='head':
  # The generated bust painted human-tan throat skin below the green jaw; restore reptile skin in that semantic area.
  z=r['pos'][:,:,2][ix[0],ix[1]];brown=(base[:,:,0]>base[:,:,1]*1.10)&(base[:,:,2]<base[:,:,1]*.98);weight=np.clip((1.505-z)/.035,0,1)*brown
  lum=base@np.array([.2126,.7152,.0722]);green=np.array([.255,.365,.135]);green/=green@np.array([.2126,.7152,.0722]);target=np.clip(lum[:,:,None]*green*.92,0,1);base=base*(1-weight[:,:,None])+target*weight[:,:,None]
  Image.fromarray(np.uint8(weight*255)).save(T/'head_neck_correction_mask.png');rep['neck_correction_pixels']=int((valid&(weight>.5)).sum())
 rough=np.where(steel,np.clip(rough,.55,.78),np.clip(rough,.72,.93));metal=np.where(steel,metal*.45,metal*.1);spec=np.where(steel,.30,.035)
 mr=np.dstack([spec,rough,metal]);mask=Image.fromarray((cloth*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45));w=np.array(mask)/255
 for n,a in [('basecolor',base),('normal',normal),('metal_rough',mr)]:Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(T/f'{tag}_{n}_1k.png')
 write_mask([w],T/f'{tag}_regions_1k.png',1024)
 np.savez_compressed(T/f'{tag}_semantic.npz',piece=pid,cloth=w)
 rep[tag]={'covered_pixels':int(valid.sum()),'cloth_pixels':int((w>.9).sum()),'skin_median_rgb':np.median(base[valid&skin],axis=0).tolist(),'steel_p95_rgb':np.percentile(base[valid&steel],95,axis=0).tolist()if (valid&steel).any()else None}
 if tag=='body':BASE=base;WEIGHT=w
# Match only the native tunic palette range; color and mask remain padded across every UV seam.
pals={n:np.fromfile(R/f'assets_dev/worlds/mm6/textures/pal{n}.act',np.uint8)[:768].reshape(256,3)/255 for n in [767,766,768]};idx=np.arange(1,36);luma=np.array([.2126,.7152,.0722]);y=pals[767][idx]@luma
counts=np.zeros(256)
for native in sorted((P.parent/'mm6_lzd/native').glob('lzd*.png')):
 rgba=np.array(Image.open(native).convert('RGBA'));rgb,count=np.unique(rgba[rgba[:,:,3]>250,:3],axis=0,return_counts=True)
 dist=((rgb[:,None,:]/255-pals[767][None,:,:])**2).sum(2);nearest=dist.argmin(1);valid=dist.min(1)<(2/255)**2
 np.add.at(counts,nearest[valid],count[valid])
assert counts[idx].sum()>100,'Native tunic palette sample missing'
curves={}
for pal in [766,768]:
 curve=[]
 for v in np.linspace(0,1,256):
  d=(y-v)**2;weights=counts[idx]*np.exp(-(d-d.min())/(32/255**2));curve.append(weights@pals[pal][idx]/max(weights.sum(),1e-8))
 curves[pal]=np.array(curve)
level=np.uint8(np.clip((BASE@luma)*255,0,255));targets={'lzd_a':BASE,'lzd_b':curves[766][level],'lzd_c':curves[768][level]}
ramps,fit=fit_ramps(BASE,targets,WEIGHT);materials=[]
for tag,name,prefix in [('body','Lizard_A','Lizard'),('head','LizardHead_A','LizardHead'),('bow','LizardBow_A','LizardBow')]:
 if tag=='bow':write_mask([np.zeros((1024,1024))],T/'bow_regions_1k.png',1024)
 materials.append({'base':name,'prefix':prefix,'mask':f'{tag}_regions_1k.png','ramps':{v:[ramps[v]]for v in ramps}})
(T/'lzd_ramps.json').write_text(json.dumps({'variants':['lzd_a','lzd_b','lzd_c'],'materials':materials},indent=2));rep['palette_fit']=fit
(P/'review/texture_validation.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
assert rep['body']['cloth_pixels']>1000
