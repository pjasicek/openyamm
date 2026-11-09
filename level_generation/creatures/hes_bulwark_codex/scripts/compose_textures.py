"""Shared atlas, padded armour/trim regions and HD-colour-derived tier ramps; no baked runtime tier skins."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'level_generation/creatures/claude_shared'),str(R/'level_generation/creatures/hes_turrets_claude/scripts')]
from raster import rasterise
from region_variants import fit_ramps,srgb_to_linear,luminance
from normal_map_convention import measure
S=P/'meshy/bulwark_retexture_v1';out=P/'textures'
load=lambda n:np.asarray(Image.open(S/f'texture_urls_0_{n}.png').convert('RGB'),np.float32)/255
base=load('base_color');normal=load('normal');rough=load('roughness');res=len(base)
d=np.load(P/'work/bulwark_tex_tris.npz');tri,pos=rasterise(d['uv'],d['co'],d['n'],res);cover=tri>=0
r,g,b=np.moveaxis(base,-1,0)
purple=(b>g*1.10)&(r>g*1.08)
metal=load('metallic')[:,:,0]
armor=(~purple)&(b>r*.46)&(g>r*.70)&(r>.18)&(metal<.65)
trim=(~purple)&(~armor)&(r>b*1.22)&(g>b*1.10)
weights=np.stack([armor,trim],-1).astype(np.float32)
# Extend only from real UV coverage so gaps cannot retain another island's region.
_,near=distance_transform_edt(~cover,return_indices=True)
weights=weights[tuple(near)];base=base[tuple(near)];normal=normal[tuple(near)];rough=rough[tuple(near)]
mask=np.zeros((res,res,4),np.uint8);mask[:,:,:2]=weights*255
# RGBA channels are four independent masks; never premultiply them by the unused alpha.
Image.merge('RGBA',[Image.fromarray(mask[:,:,i]).resize((1024,1024),Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(.5)) for i in range(4)]).save(out/'bulwark_region_mask.png')
# The current engine uses ORM.R as a specular mask, not AO. Keep the AO source separately.
ao=np.asarray(Image.open(out/'bulwark_ao.png').convert('L').resize((res,res),Image.Resampling.BILINEAR),float)/255
base=np.clip(base*(.75+.25*ao[:,:,None]),30/255,243/255)
specular=np.where(weights[:,:,0]>.5,.60,np.where(weights[:,:,1]>.5,.85,.30))
rough_min=np.where(weights[:,:,0]>.5,.55,np.where(weights[:,:,1]>.5,.42,.64))
orm=np.stack([specular,np.maximum(rough[:,:,0],rough_min),np.clip(weights.sum(-1),0,1)],-1)
correlation=float(measure(np.asarray(Image.open(S/'texture_urls_0_normal.png').convert('RGB'))))
if correlation<=-.15:normal[:,:,1]=1-normal[:,:,1]
for name,a,size in [('basecolor',base,2048),('normal',normal,1024),('orm',orm,1024)]:
 Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).resize((size,size),Image.Resampling.LANCZOS).save(out/f'bulwark_{name}.png')
labels=np.where(weights[:,:,0]>.5,5,np.where(weights[:,:,1]>.5,9,11)).astype(np.uint8);labels[~cover]=0
Image.fromarray(labels).resize((1024,1024),Image.Resampling.NEAREST).save(out/'bulwark_material_classes.png')
# Triangles are assigned by full-face texel coverage, never by a single UV-centre sample.
counts=np.bincount(tri[cover],minlength=len(d['uv']));means=[]
for channel in range(2):
 sums=np.bincount(tri[cover],weights=weights[:,:,channel][cover],minlength=len(d['uv']))
 means.append(sums/np.maximum(counts,1))
faceclass=np.where(means[0]>.45,0,np.where(means[1]>.45,1,2))
# Subpixel triangles inherit the nearest atlas texel at their UV centre.
u=d['uv'].mean(1);x=np.clip((u[:,0]*res).astype(int),0,res-1);y=np.clip(((1-u[:,1])*res).astype(int),0,res-1)
faceclass[counts==0]=np.where(weights[y[counts==0],x[counts==0],0]>.45,0,np.where(weights[y[counts==0],x[counts==0],1]>.45,1,2))
np.save(P/'work/bulwark_face_materials.npy',faceclass)
# Reuse the independently measured Sentinel family palettes; fit this model's own luminance range.
family=json.loads((P.parent/'hes_sentinel_codex/textures/sentinel_ramps.json').read_text())['materials'][0]['ramps']
base1=np.asarray(Image.open(out/'bulwark_basecolor.png').resize((1024,1024)),float)/255
mask1=np.asarray(Image.open(out/'bulwark_region_mask.png'),float)/255
ramps={v:[] for v in ['bulwark_a','bulwark_b','bulwark_c']};errors={};palettes={}
for ch in range(2):
 fit,err=fit_ramps(base1,{'bulwark_a':base1},mask1[:,:,ch]);ramps['bulwark_a'].append(fit['bulwark_a']);errors[str(ch)]=err
 for variant,subject,region in [('bulwark_b','heavy_bulwark','bone' if ch==0 else 'gold'),('bulwark_c','crown_bulwark','gold')]:
  src=family['sentinel_'+variant[-1]][ch]
  palettes[f'{variant}_{ch}']=src['colors']
  ramps[variant].append({'range':fit['bulwark_a']['range'],'colors':src['colors']})
cfg={'variants':list(ramps),'materials':[{'base':mat,'prefix':mat,'mask':'bulwark_region_mask.png','ramps':ramps} for mat in ['Bulwark_Armour','Bulwark_Trim','Bulwark_Resin']]}
(out/'bulwark_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report={'normal_correlation':correlation,'normal_green_flipped':correlation<=-.15,'face_material_counts':np.bincount(faceclass,minlength=3).tolist(),'regions':['ivory armour','bronze trim'],'unchanged':'violet resin','region_texel_counts':[int(((weights[:,:,i]>.5)&cover).sum()) for i in range(2)],'fit_A':errors,'HD_palette_samples_srgb':palettes,'orm_red':'per-texel specular mask; AO retained separately','palette_source':'hes_sentinel_codex/textures/sentinel_ramps.json','ao_grade_strength':.25,'material_classes':{'5':'ivory armour (gilded on C)','9':'metal trim','11':'violet resin'}}
(out/'bulwark_material_report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='HD_palette_samples_srgb'})
