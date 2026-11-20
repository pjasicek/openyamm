"""Compose one padded atlas, material classes and hbm region ramps from the preserved Meshy return."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import distance_transform_edt,map_coordinates
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.dont_write_bytecode=True
sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared'),str(P.parent/'hes_turrets_claude/scripts')]
from raster import rasterise
from region_variants import fit_ramps
from normal_map_convention import measure
S=P/'meshy/brood_mother_texture_v2';D=P/'textures';D.mkdir(exist_ok=True)
d=np.load(P/'work/texture_transfer.npz');size=2048
uv=d['patch_uv'];yx=d['patch_pixels'];maps={}
for name in ['base_color','normal','roughness','metallic']:
 im=Image.open(S/f'texture_urls_0_{name}.png').convert('RGB');source=np.asarray(im,float)/255
 out=np.zeros((size,size,3));out[:1920]=np.asarray(im.resize((size,1920),Image.Resampling.LANCZOS),float)/255
 values=np.stack([map_coordinates(source[:,:,c],[(1-uv[:,:,1])*(len(source)-1),uv[:,:,0]*(len(source)-1)],order=1,mode='nearest') for c in range(3)],-1)
 values=(values*d['patch_weights'][:,:,None]).sum(1)
 if name=='normal':values[:]=[.5,.5,1] # Projected patches have new tangent frames; keep their geometric normals.
 out[yx[:,0],yx[:,1]]=values;maps[name]=out
tri,pos=rasterise(d['uvs'],d['triangles'],None,size);cover=tri>=0
_,near=distance_transform_edt(~cover,return_indices=True)
base=maps['base_color'];r,g,b=np.moveaxis(base,-1,0)
purple=(b>g*1.035)&(r>g*1.025)
ivory=(~purple)&(b>r*.40)&(g>r*.60)&(r>.16)&(maps['metallic'][:,:,0]<.75)
gold=(~purple)&(~ivory)&(r>b*1.2)&(g>b*1.1)&(r>.18)
weights=np.stack([purple,ivory,gold],-1).astype(float)[tuple(near)]
base=np.clip(base[tuple(near)],20/255,243/255)
normal=maps['normal'][tuple(near)]
corr=float(measure(np.asarray(Image.open(S/'texture_urls_0_normal.png').convert('RGB'))))
if corr<=-.15:normal[:,:,1]=1-normal[:,:,1]
rough=np.maximum(maps['roughness'][:,:,0][tuple(near)],np.where(weights[:,:,0]>.5,.72,np.where(weights[:,:,1]>.5,.56,.42)))
spec=np.where(weights[:,:,0]>.5,.25,np.where(weights[:,:,1]>.5,.4,np.where(weights[:,:,2]>.5,.8,.2)))
metal=np.where(weights[:,:,2]>.5,.65,0.)
mr=np.stack([spec,rough,metal],-1)
for name,a,res in [('basecolor',base,2048),('normal',normal,1024),('metal_rough',mr,1024)]:
 im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).resize((res,res),Image.Resampling.LANCZOS)
 if name=='normal':
  n=np.asarray(im,float)/127.5-1;n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8);im=Image.fromarray(np.uint8(np.clip(n*.5+.5,0,1)*255+.5))
 im.save(D/f'hbm_{name}.png')
channels=[Image.fromarray(np.uint8(weights[:,:,i]*255)).resize((1024,1024),Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(.5)) for i in range(3)]
channels.append(Image.new('L',(1024,1024),0));Image.merge('RGBA',channels).save(D/'hbm_region_mask.png')
classes=np.where(purple,1,np.where(ivory,5,np.where(gold,9,11))).astype(np.uint8);classes[~cover]=0
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(D/'hbm_material_classes.png')
b1=np.asarray(Image.open(D/'hbm_basecolor.png').resize((1024,1024)),float)/255
m1=np.asarray(Image.open(D/'hbm_region_mask.png'),float)/255
ramps=[];errors=[]
for ch in range(3):
 target=b1
 if ch in (1,2):
  grey=b1@np.array([.2126,.7152,.0722]);tint=np.array([1.10,1.03,.88]) if ch==1 else np.array([1.40,1.08,.50])
  target=np.clip((grey**(.80 if ch==1 else .85))[:,:,None]*tint,0,.95)
 fits,err=fit_ramps(b1,{'hbm':target},m1[:,:,ch]);ramps.append(fits['hbm']);errors.append(err)
config={'variants':['hbm'],'materials':[{'base':'BroodMotherSurface','prefix':'BroodMotherSurface','mask':'hbm_region_mask.png','ramps':{'hbm':ramps}}]}
(D/'hbm_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
report={'normal_correlation':corr,'normal_green_flipped':corr<=-.15,'regions':['violet skin/resin','ivory chitin','gold trim'],'fit_hbm':errors,'map_sizes':{'base':2048,'normal_mr_region':1024},'mr_red':'specular mask, not AO','classes':{'1':'violet skin/resin','5':'ivory chitin','9':'gold trim','11':'dark details'},'patched_faces':22,'patch_normal':'neutral in new UV frame','finish':'Ivory ramp removes brown cast, gold ramp restores warm trim; base detail remains shared','emission':'none; egg-sac emission belongs to 10130'}
(D/'material_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
