"""Shared 2K skin, 1K normal/specular maps and native 601/602/603 skin/iris ramps."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
src=P/'meshy/body_texture_v1';r=np.load(P/'work/uvraster_UVMap.npz');piece=r['piece'];cov=piece>=0
load=lambda f,mode='RGB':np.asarray(Image.open(src/f).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
base=load('texture_urls_0_base_color.png');normal=load('texture_urls_0_normal.png');rough=load('texture_urls_0_roughness.png','L')
skin=(piece==0);eyes=(piece==1);teeth=(piece==2)
red=(base[:,:,0]>base[:,:,1]*1.35)&(base[:,:,0]>base[:,:,2]*1.3)
iris=eyes&red
# Inner mouths keep their dark warm tissue instead of inheriting the body colour ramp.
skin &= ~red
# The green socket skin belongs to the tier; sclera and red iris keep separate regions.
eye_rim=eyes & (base[:,:,2] < .8*np.minimum(base[:,:,0],base[:,:,1])) & (base[:,:,1] > .82*base[:,:,0]) & (base[:,:,1] < 1.4*base[:,:,0])
skin |= eye_rim
idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
base=np.clip(base,0,1)[tuple(idx)]
enc=lambda c:np.where(c<=.0031308,12.92*c,1.055*np.maximum(c,0)**(1/2.4)-.055)
lin=R.srgb_to_linear(base);lum=lin@R.LUMA
# A modest neutral grade retains the painted mottling; all tier hue changes use measured native palette ratios.
lin[(piece==0)&~red]*=.82;base=np.clip(enc(lin),0,1)
Image.fromarray(np.uint8(base*255+.5)).save(T/'body_basecolor.png')
Image.fromarray(np.uint8(normal[tuple(idx)]*255+.5)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'body_normal.png')
spec=np.where(eyes,.6,np.where(teeth,.3,.55));roughness=np.where(eyes,.36,np.where(teeth,.55,.58+.10*(rough-.5)))
orm=np.stack([spec,roughness,np.zeros_like(spec)],-1)[tuple(idx)]
Image.fromarray(np.uint8(np.clip(orm,0,1)*255+.5)).resize((1024,1024),Image.Resampling.BOX).save(T/'body_orm.png')
regions=[nd.gaussian_filter(m.astype(float)[tuple(idx)],.6) for m in [skin,iris]]
R.write_mask(regions,T/'body_region_mask.png',1024)
# Native indices preserve paired tier correspondence (sorting each tier separately would mix anatomical regions).
inv=json.loads((P/'references_native/inventory.json').read_text())
pals=[np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for n in [601,602,603]]
indices=np.concatenate([np.array(Image.open(P.parents[2]/inv['sources'][f]['path'])).ravel() for f in ['m600sa0','m600wa0','m600wc2','m600na0']])
pa=pals[0];sel_skin=(pa[:,1]>pa[:,0]*1.02)&(pa[:,1]>pa[:,2]*1.05);sel_skin[0]=False
sel_iris=(pa[:,0]>pa[:,1]*1.7)&(pa[:,0]>pa[:,2]*1.5)&(pa[:,0]>.2)
ramps={f'nightmare_{x}':[] for x in 'abc'};reports=[]
for weight,selection in zip(regions,[sel_skin,sel_iris]):
 core=weight>.9;assert core.sum()>100
 ids=indices[selection[indices]];assert len(ids)>100
 lums=R.srgb_to_linear(pa[ids])@R.LUMA;ids=ids[np.argsort(lums)]
 current=R.luminance(base);order=np.argsort(current[core]);rank=np.empty(len(order));rank[order]=(np.arange(len(order))+.5)/len(order)
 chosen=ids[np.minimum((rank*len(ids)).astype(int),len(ids)-1)];a=R.srgb_to_linear(pa[chosen]);den=np.maximum(a@R.LUMA,.001)
 targets={}
 for k,pal in enumerate(pals):
  b=R.srgb_to_linear(pal[chosen]);target=base.copy();target[core]=np.clip(enc(current[core,None]*b/den[:,None]),0,1)
  targets[f'nightmare_{"abc"[k]}']=target
 fitted,report=R.fit_ramps(base,targets,weight)
 for k in ramps:ramps[k].append(fitted[k])
 reports.append(report)
cfg={'variants':list(ramps),'materials':[{'base':'Nightmare','prefix':'NightmareSkin','mask':'body_region_mask.png','regions':['skin','iris'],'ramps':ramps}],'palette_ids':[601,602,603],'method':'Paired native index chroma and tier luminance ratios, preserving the generated albedo detail'}
(T/'nightmare_ramps.json').write_text(json.dumps(cfg,indent=2))
(T/'texture_report.json').write_text(json.dumps({'fit':reports,'class_pixels':{'skin':int(skin.sum()),'eyes':int(eyes.sum()),'iris':int(iris.sum()),'teeth':int(teeth.sum())},'orm':'R specular mask, G roughness, B zero','basecolor':2048,'normal_orm_mask':1024},indent=2))
print('COMPOSED',reports)
