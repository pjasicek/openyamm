"""Shared body/head maps, material classes and native cloth ramps; no baked runtime tier copies."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];T=P/'textures';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(ROOT/'tools'));from merge_head_material import read_glb,accessor_array
N=1024
load=lambda p:np.asarray(Image.open(p).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
save=lambda p,a:Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
encode=lambda a:np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
# The head job is UV-preserving; prove per-corner equality before applying its maps.
a,ab=read_glb(P/'work/head_retexture.glb');b,bb=read_glb(P/'meshy/head_retexture_v1/model_urls_glb.glb');ap=a['meshes'][0]['primitives'][0];bp=b['meshes'][0]['primitives'][0];au=accessor_array(a,ab,ap['attributes']['TEXCOORD_0'])[accessor_array(a,ab,ap['indices']).ravel()];bu=accessor_array(b,bb,bp['attributes']['TEXCOORD_0'])[accessor_array(b,bb,bp['indices']).ravel()];assert np.array_equal(au,bu)
sets={}
for tag,layer in [('body','UVMap'),('head','HeadUV')]:
 M=P/f'meshy/{tag}_retexture_v1';raster=np.load(P/f'work/uvraster_{layer}.npz');valid=raster['piece']>=0;near=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True);parts=raster['piece'][tuple(near)];pos=raster['pos'][tuple(near)];raw=load(M/'texture_urls_0_base_color.png');ao=load(T/f'jak1_{tag}_ao.png')[...,0];ao=ao[tuple(near)];base=raw*(.84+.16*ao[...,None]);red,green,blue=raw.transpose(2,0,1)
 cloth=np.clip((blue-red-.02)/.06,0,1)*np.clip((blue-green-.008)/.035,0,1)*np.isin(parts,[1,2]);cloth=ndimage.gaussian_filter(cloth[tuple(near)],.5)
 yellow=(red>.15)&(green>red*.43)&(blue<green*.75)
 gold=(yellow&np.isin(parts,[0,1,2,3,4,5,6,9,10,11])) if tag=='body' else (yellow&np.isin(parts,[0,2]))
 base[gold]*=np.array([.88,.77,.80])
 classes=np.ones((N,N),np.uint8);classes[np.isin(parts,[1,2,5,6,7,8])]=8;classes[gold]=9
 eye=(tag=='head')&(parts==0)&yellow&(pos[...,2]>1.58)&(pos[...,2]<1.68)&(pos[...,1]<-.035);classes[eye]=6
 rough=load(M/'texture_urls_0_roughness.png')[...,0];rough=np.where(classes==9,np.clip(rough,.45,.70),np.maximum(rough,.77));rough[eye]=.28
 spec=np.where(classes==9,.65,np.where(classes==8,.03,.09));spec[eye]=.45;spec*=.55+.45*ao
 metal=np.where(classes==9,load(M/'texture_urls_0_metallic.png')[...,0],0);mr=np.stack([spec,rough,metal],-1)
 sets[tag]={'base':base,'cloth':cloth,'classes':classes,'pos':pos,'parts':parts,'valid':valid,'near':near,'normal':load(M/'texture_urls_0_normal.png'),'mr':mr}
# Match only dark skin across the head/neck seam, leaving eyes and cloth unchanged.
med={}
for tag,d in sets.items():
 z=d['pos'][...,2];band=(z>1.46)&(z<1.53)&(d['classes']==1)&d['valid'];med[tag]=float(np.median(R.luminance(d['base'])[band]))
gain=float(np.clip(med['body']/max(med['head'],1e-6),.65,1.5));d=sets['head'];skin=d['classes']==1;d['base'][skin]=encode(R.srgb_to_linear(d['base'][skin])*gain)
# Match the exposed native charcoal skin, dropping near-black silhouette pixels and the staff column.
native={};skin_report={'albedo_linear_gain':1.30,'native_frames':['jak1sta0','jak1wka0','jak1wkc0','jak1wke0'],'regions':{}}
for tag in ('body','head'):
 samples=[]
 for stem in skin_report['native_frames']:
  rgba=np.asarray(Image.open(P.parent/f'mm6_jak1/native/{stem}.png').convert('RGBA'));rgb=rgba[...,:3]/255;yy,xx=np.mgrid[:rgb.shape[0],:rgb.shape[1]];blue=(rgb[...,2]>rgb[...,0]+.08)&(rgba[...,3]>0);cx=float(np.median(xx[blue]));lum=rgb@R.LUMA
  region=(xx>cx-37)&(xx<cx+45)&(yy>145)&(yy<340) if tag=='body' else (xx>cx-17)&(xx<cx+17)&(yy>90)&(yy<145)
  mask=region&(rgba[...,3]>0)&(np.ptp(rgb,2)<8/255)&(lum>16/255)
  samples.extend(lum[mask].tolist())
 native[tag]=np.array(samples)
 d=sets[tag];skin=(d['classes']==1);core=skin&d['valid'];lum=R.luminance(d['base']);qs=np.linspace(0,1,257);x=np.quantile(lum[core],qs);ys=np.quantile(native[tag],qs);target_linear=np.where(ys<=.04045,ys/12.92,((ys+.055)/1.055)**2.4)*1.30
 x,unique=np.unique(x,return_index=True);target_linear=target_linear[unique];graded=np.interp(lum,x,target_linear);d['base'][skin]=encode(graded[skin,None]);d['skin']=ndimage.gaussian_filter(skin.astype(float)[tuple(d['near'])],.5)
 def stats(v):return {'count':int(len(v)),'mean_srgb_255':float(np.mean(v)*255),'percentiles_srgb_255':{str(q):float(np.percentile(v,q)*255) for q in [5,25,50,75,95,98]}}
 skin_report['regions'][tag]={'native':stats(native[tag]),'before':stats(encode(lum[core])),'graded':stats(encode(graded[core]))}
 assert skin_report['regions'][tag]['graded']['mean_srgb_255']>skin_report['regions'][tag]['native']['mean_srgb_255']
(T/'skin_luminance.json').write_text(json.dumps(skin_report,indent=2))
variants=['jak1_a','jak1_b','jak1_c'];pal={k:np.frombuffer((ROOT/f'assets_dev/worlds/mm6/textures/pal{k}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k in [757,758,759]};ids=np.r_[154:182,183:190];xs=R.srgb_to_linear(pal[757][ids])@R.LUMA;order=np.argsort(xs);xs=xs[order];base=np.concatenate([d['base']for d in sets.values()]);mask=np.concatenate([d['cloth']for d in sets.values()]);lum=R.luminance(base);targets={}
for v,k in zip(variants,[757,758,759]):
 colors=R.srgb_to_linear(pal[k][ids[order]]);mapped=np.stack([np.interp(lum,xs,colors[:,i])for i in range(3)],-1);targets[v]=np.clip(encode(mapped),0,1)
base=base*(1-mask[...,None])+targets['jak1_a']*mask[...,None]
for i,d in enumerate(sets.values()):d['base']=base[i*N:(i+1)*N]
targets['jak1_a']=base
ramps,fit=R.fit_ramps(base,targets,mask,core_threshold=.8);materials=[]
for tag,d in sets.items():
 stem=f'jak1_{tag}';save(T/f'{stem}_basecolor_1k.png',d['base']);save(T/f'{stem}_normal_1k.png',d['normal']);save(T/f'{stem}_metal_rough_1k.png',d['mr']);R.write_mask([d['cloth'],d['skin']],T/f'{stem}_region_mask.png',1024);Image.fromarray(d['classes']).save(T/f'{stem}_material_classes.png');name='Jackalman_A' if tag=='body' else 'JackalmanHead_A';materials.append({'base':name,'prefix':name[:-2],'mask':f'{stem}_region_mask.png','regions':['native blue/purple/red cloth','native charcoal skin'],'ramps':{v:[ramps[v],{'range':[0.0,1.0],'colors':[[j/15]*3 for j in range(16)]}]for v in variants}})
# The staff keeps its native colours across tiers and has no colour-region entry.
(T/'jak1_ramps.json').write_text(json.dumps({'variants':variants,'materials':materials},indent=2));(T/'composition.json').write_text(json.dumps({'native_palettes':[757,758,759],'native_cloth_indices':ids.tolist(),'head_uv_per_corner_identical':True,'head_skin_seam_gain':gain,'seam_linear_medians':med,'ramp_fit':fit,'MR_red':'specular mask, AO separately retained','classes':{'1':'skin','6':'eyes','8':'cloth/leather','9':'metal','10':'staff wood','11':'staff cyan enamel'},'runtime_maps':1024},indent=2));print('COMPOSE',gain,fit,flush=True)
