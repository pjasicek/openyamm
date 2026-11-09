"""Shared detailed maps, native equipment ramps and measured warm-brown skin; no paid tier textures."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];T=P/'textures';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(ROOT/'tools'));from normal_map_convention import measure
N=1024;LUMA=R.LUMA;normal_reports={}
encode=lambda a:np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
load=lambda p:np.asarray(Image.open(p).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
save=lambda p,a:Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
# Native original pixels, excluding cyan matte and near-black silhouette/shadow rims.
nat=np.asarray(Image.open(P.parent/'mm6_natm/native/natmsta0.png').convert('RGBA'));native={};samples=[]
for tag,(x0,y0,x1,y1)in {'head':(164,62,190,96),'body':(150,132,205,170),'legs':(145,197,158,239)}.items():
 rgb=nat[y0:y1,x0:x1,:3]/255;lum=rgb@LUMA;mask=(rgb[...,0]>rgb[...,1]*1.05)&(rgb[...,1]>rgb[...,2]*1.05)&(lum>.04);native[tag]=rgb[mask];samples.extend(rgb[mask].tolist())
colors=np.array(samples);lum=colors@LUMA;order=np.argsort(lum);colors=colors[order];lum=lum[order];qs=np.linspace(0,1,257);indices=np.linspace(0,len(colors)-1,257).astype(int);ramp=R.srgb_to_linear(colors[indices]);chroma=np.median(ramp/np.maximum(ramp@LUMA,1e-8)[:,None],axis=0);chroma/=chroma@LUMA
# Native pixels include their painted shadows. The small albedo lift avoids applying that darkness twice in game light.
ramp=np.clip(ramp*1.30+chroma[None,:]*.012,0,1);graded_colors=encode(ramp)
sets={};skin_report={'native_source':'../mm6_natm/native/natmsta0.png','native_rois':{'head':[164,62,190,96],'body':[150,132,205,170],'legs':[145,197,158,239]},'linear_gain':1.30,'linear_shadow_floor':.012,'regions':{}}
def stats(rgb):
 v=rgb@LUMA;return {'pixels':len(v),'mean_srgb_255':float(v.mean()*255),'percentiles_srgb_255':{str(q):float(np.percentile(v,q)*255) for q in [5,25,50,75,95,98]}}
for tag,layer in [('body','UVMap'),('head','HeadUV'),('spear','Spear'),('buckler','Buckler')]:
 r=np.load(P/f'work/uvraster_{layer}.npz');valid=r['piece']>=0;near=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True);parts=r['piece'][tuple(near)];pos=r['pos'][tuple(near)];job=P/f'meshy/{tag}_retexture_v1';raw=load(job/'texture_urls_0_base_color.png');base=raw.copy();red,green,blue=raw.transpose(2,0,1)
 skin=np.zeros((N,N),bool);cloth=np.zeros((N,N),float);steel=np.zeros((N,N),bool)
 if tag in ['body','head']:
  skin=parts==0;core=skin&valid;v=R.luminance(raw);x=np.quantile(v[core],qs);x,unique=np.unique(x,return_index=True);mapped=np.stack([np.interp(v,x,graded_colors[unique,j])for j in range(3)],-1);base[skin]=mapped[skin]
  cloth=np.isin(parts,[1,10,12,15]).astype(float) if tag=='body' else cloth
  green_seed=(green>red*.95)&(blue<green*.67)&(green>.05)
  cloth=np.maximum(cloth,green_seed&~skin&~np.isin(parts,[2,3]))
  sample=native['body'] if tag=='body' else native['head'];skin_report['regions'][tag]={'native':stats(sample),'raw':stats(raw[core]),'graded':stats(base[core])}
  assert skin_report['regions'][tag]['graded']['mean_srgb_255']>skin_report['regions'][tag]['native']['mean_srgb_255']
 elif tag=='spear':
  z=pos[...,2];cloth=((z>.320)&(z<.382)|((z>.742)&(z<.815))).astype(float);steel=z>.815;lum=raw@LUMA;base[steel]=np.clip(lum[steel,None]*np.array([.75,.78,.79]),.08,.60)
 else:cloth=(pos[...,1]<.011).astype(float)
 cloth=ndimage.gaussian_filter(cloth,.40);rough=load(job/'texture_urls_0_roughness.png')[...,0];rough=np.maximum(rough,.78);rough[steel]=np.clip(rough[steel],.53,.70);spec=np.where(steel,.50,np.where(skin,.075,.035));normal=load(job/'texture_urls_0_normal.png');corr=measure(np.uint8(normal*255+.5));normal_reports[tag]={'source_correlation':corr,'green_flipped':bool(corr<=-.15)}
 if corr<=-.15:normal[...,1]=1-normal[...,1]
 mr=np.stack([spec,rough,np.zeros_like(rough)],-1)
 sets[tag]={'base':base,'cloth':cloth,'skin':ndimage.gaussian_filter(skin.astype(float),.40),'valid':valid,'normal':normal,'mr':mr}
# The palette's equipment entries retain their measured native chroma and relative tier brightness.
pal={k:np.frombuffer((ROOT/f'assets_dev/worlds/mm6/textures/pal{k}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k in [795,796,797]};ids=np.arange(6,97);pbase=R.srgb_to_linear(pal[796][ids]);lum0=pbase@LUMA;order=np.argsort(lum0);lum0=lum0[order];ids=ids[order];use=lum0>.002;lum0=lum0[use];ids=ids[use]
base=np.concatenate([d['base']for d in sets.values()]);mask=np.concatenate([d['cloth']for d in sets.values()]);skinmask=np.concatenate([d['skin']for d in sets.values()]);v=R.luminance(base);targets={}
for variant,k in [('natm_a',795),('natm_b',796),('natm_c',797)]:
 lin=R.srgb_to_linear(pal[k][ids]);ratios=lin/np.maximum(lum0[:,None],.002);ch=np.stack([np.interp(np.clip(v,lum0[0],lum0[-1]),lum0,ratios[:,j]) for j in range(3)],-1);targets[variant]=np.clip(encode(v[...,None]*ch),0,1)
base=base*(1-mask[...,None])+targets['natm_b']*mask[...,None]
cloth_ramps,clothfit=R.fit_ramps(base,targets,mask,core_threshold=.9);skin_ramps,skinfit=R.fit_ramps(base,{k:base for k in targets},skinmask,core_threshold=.9)
materials=[]
for i,(tag,d)in enumerate(sets.items()):
 d['base']=base[i*N:(i+1)*N];stem=f'natm_{tag}';save(T/f'{stem}_basecolor.png',d['base']);save(T/f'{stem}_normal.png',d['normal']);save(T/f'{stem}_metal_rough.png',d['mr']);R.write_mask([d['cloth'],d['skin']],T/f'{stem}_region_mask.png',N)
 name={'body':'Natm_B','head':'NatmHead_B','spear':'NatmSpear_B','buckler':'NatmBuckler_B'}[tag];materials.append({'base':name,'prefix':name[:-2],'mask':f'{stem}_region_mask.png','regions':['native equipment','native warm-brown skin'],'ramps':{v:[cloth_ramps[v],skin_ramps[v]] for v in targets}})
(T/'natm_ramps.json').write_text(json.dumps({'variants':list(targets),'materials':materials},indent=2));(T/'skin_luminance.json').write_text(json.dumps(skin_report,indent=2));(T/'composition.json').write_text(json.dumps({'tier_palettes':{'A':795,'B':796,'C':797},'native_equipment_indices':ids.tolist(),'cloth_fit':clothfit,'skin_fit':skinfit,'MR_red':'specular mask, not AO','steel_srgb_cap':.60,'resolution':1024,'normal_convention':normal_reports},indent=2));print('TEXTURES',skin_report['regions'],clothfit,skinfit,flush=True)
