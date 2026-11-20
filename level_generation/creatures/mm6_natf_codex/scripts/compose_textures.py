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
a,ab=read_glb(P/'work/head_retexture.glb');b,bb=read_glb(P/'meshy/head_retexture_v1/model_urls_glb.glb');ap=a['meshes'][0]['primitives'][0];bp=b['meshes'][0]['primitives'][0];au=accessor_array(a,ab,ap['attributes']['TEXCOORD_0'])[accessor_array(a,ab,ap['indices']).ravel()];bu=accessor_array(b,bb,bp['attributes']['TEXCOORD_0'])[accessor_array(b,bb,bp['indices']).ravel()];assert np.array_equal(au,bu)
ref=json.loads((P/'source/native_skin_baseline.json').read_text())['measurements']['795'];native=np.asarray(Image.open(ROOT/ref['path']).convert('RGBA'));samples={}
for name,row in ref['rois'].items():
 x0,y0,x1,y1=row['roi_xyxy'];r=native[y0:y1,x0:x1];samples[name]=r[...,:3][r[...,3]>128]/255
pooled=np.concatenate(list(samples.values()));sets={};skin_report={}
for tag,layer in [('body','UVMap'),('head','HeadUV')]:
 M=P/f'meshy/{tag}_retexture_v1';raster=np.load(P/f'work/uvraster_{layer}.npz');valid=raster['piece']>=0;near=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True);parts=raster['piece'][tuple(near)];pos=raster['pos'][tuple(near)];raw=load(M/'texture_urls_0_base_color.png');ao=load(T/f'natf_{tag}_ao.png')[...,0][tuple(near)];base=raw*(.88+.12*ao[...,None]);red,green,blue=raw.transpose(2,0,1)
 if tag=='body':
  skin=(parts==1)|((parts==0)&(red>green*1.17)&(green>blue*1.04)&((pos[...,2]>1.03)|(np.abs(pos[...,0])>.24)))
  cloth=(parts==0)&~skin&(green>red*.88)&(green>blue*1.15)
  gold=np.isin(parts,[4,6,7,10,11,12,13,14,15])
 else:
  skin=(parts==0)&(red>green*1.17)&(green>blue*1.035);cloth=(parts==0)&~skin&(green>red*.88)&(green>blue*1.15)&(pos[...,2]>1.43);gold=(parts==0)&~skin&~cloth&(red>blue*1.45)
 hair=np.isin(parts,[3,5]);eye=np.isin(parts,[8,9]);classes=np.full((N,N),8,np.uint8);classes[skin]=1;classes[hair]=4;classes[eye]=6;classes[gold]=9
 # Preserve hue and detail; fit linear luminance to the native samples, including highlight percentiles.
 target=samples['face'] if tag=='head'else pooled;targetlum=R.luminance(target)*1.05;lum=R.luminance(base);core=skin&valid;assert core.sum()>1000;qs=np.linspace(0,1,1025);xx=np.quantile(lum[core],qs);yy=np.quantile(targetlum,qs);xx,ind=np.unique(xx,return_index=True);mapped=np.interp(lum,xx,yy[ind]);linear=R.srgb_to_linear(base);linear[skin]*=(mapped[skin]/np.maximum(lum[skin],1e-8))[:,None];base=encode(linear)
 if hair.any():
  gain=.010/max(float(R.luminance(base)[hair&valid].mean()),1e-6);base[hair]=encode(R.srgb_to_linear(base[hair])*gain)
 def stats(v):return {'mean':float(np.mean(v)),'p90':float(np.percentile(v,90)),'p95':float(np.percentile(v,95))}
 actual=R.luminance(np.round(np.clip(base,0,1)*255)/255)[core];native_stats=stats(R.luminance(target));skin_report[tag]={'reference':'native face ROI'if tag=='head'else'native pooled face/abdomen/calves','native':native_stats,'graded':stats(actual),'texels':int(core.sum()),'linear_gain':1.05}
 assert all(skin_report[tag]['graded'][k]>=native_stats[k]*.995 for k in native_stats)
 rough=load(M/'texture_urls_0_roughness.png')[...,0];rough=np.maximum(rough,.78);rough[gold]=.62;rough[eye]=.32;spec=np.where(gold,.45,np.where(eye,.32,np.where(skin,.07,.025)));spec*=.65+.35*ao;metal=np.where(gold,.45,0);mr=np.stack([spec,rough,metal],-1)
 sets[tag]={'base':base,'cloth':ndimage.gaussian_filter(cloth.astype(float),.6),'skin':ndimage.gaussian_filter(skin.astype(float),.5),'normal':load(M/'texture_urls_0_normal.png'),'mr':mr,'classes':classes}
# The shield's olive front shares the native equipment ramp; its leather rear remains brown.
raw=load(T/'shield_basecolor_1k.png');r,g,b=raw.transpose(2,0,1);mask=(g>r*.88)&(g>b*1.3)&(r>b*1.2);sets['shield']={'base':raw,'cloth':ndimage.gaussian_filter(mask.astype(float),.6),'skin':np.zeros((N,N)),'mr':load(T/'shield_metal_rough_1k.png'),'classes':np.full((N,N),8,np.uint8)}
variants=['natf_a','natf_b','natf_c'];pal={k:np.frombuffer((ROOT/f'assets_dev/worlds/mm6/textures/pal{k}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k in [795,796,797]};ids=np.where(np.any(pal[795]!=pal[796],axis=1)|np.any(pal[796]!=pal[797],axis=1))[0];xs=R.luminance(pal[796][ids]);order=np.argsort(xs);xs=xs[order];base=np.concatenate([d['base']for d in sets.values()]);mask=np.concatenate([d['cloth']for d in sets.values()]);lum=R.luminance(base);targets={}
for v,k in zip(variants,[795,796,797]):
 colors=R.srgb_to_linear(pal[k][ids[order]]);mapped=np.stack([np.interp(lum,xs,colors[:,i])for i in range(3)],-1);targets[v]=np.clip(encode(mapped),0,1)
base=base*(1-mask[...,None])+targets['natf_a']*mask[...,None]
for i,d in enumerate(sets.values()):d['base']=base[i*N:(i+1)*N]
targets['natf_a']=base;ramps,fit=R.fit_ramps(base,targets,mask,core_threshold=.8);skinmask=np.concatenate([d['skin']for d in sets.values()]);skinramps,skinfit=R.fit_ramps(base,{v:base for v in variants},skinmask,core_threshold=.8);materials=[]
for tag,d in sets.items():
 stem=f'natf_{tag}';save(T/f'{stem}_basecolor_1k.png',d['base']);save(T/f'{stem}_metal_rough_1k.png',d['mr']);Image.fromarray(d['classes']).save(T/f'{stem}_material_classes.png');R.write_mask([d['cloth'],d['skin']],T/f'{stem}_region_mask.png',1024)
 if 'normal'in d:save(T/f'{stem}_normal_1k.png',d['normal'])
 name={'body':'Natf_A','head':'NatfHead_A','shield':'LeafShield_A'}[tag];materials.append({'base':name,'prefix':name[:-2],'mask':f'{stem}_region_mask.png','regions':['native equipment','unchanged native skin'],'ramps':{v:[ramps[v],skinramps[v]]for v in variants}})
(T/'natf_ramps.json').write_text(json.dumps({'variants':variants,'materials':materials},indent=2));(T/'skin_luminance.json').write_text(json.dumps(skin_report,indent=2));(T/'composition.json').write_text(json.dumps({'native_palettes':[795,796,797],'indices':ids.tolist(),'head_uv_per_corner_identical':True,'ramp_fit':fit,'skin_ramp_fit':skinfit,'MR_red':'specular mask; AO retained separately','runtime_maps':1024,'body_credits':10,'head_credits':10},indent=2));print('COMPOSITION',skin_report,fit,flush=True)
