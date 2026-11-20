"""Compose the corrected head and welded neck; preserve the accepted body's existing textures and spike ramps."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
p=Path(__file__).resolve().parents[1];t=p/'textures';N=1024
load=lambda f:np.asarray(Image.open(f).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
save=lambda a,f:Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(f,optimize=True)
r=np.load(p/'work/uvraster_UVMap.npz');hr=np.load(p/'work/uvraster_HeadUV.npz');cov=r['piece']>=0;hcov=hr['piece']>=0;pos=r['pos'];hp=hr['pos']
base=load(t/'ogr_basecolor_1k.png');normal=load(t/'ogr_normal_1k.png');mr=load(t/'ogr_metal_rough_1k.png');bc=np.array(Image.open(t/'ogr_material_classes.png'))
new=cov&(bc==0);raw=load(p/'meshy/retexture_v1/texture_urls_0_base_color.png');rn=load(p/'meshy/retexture_v1/texture_urls_0_normal.png')
base[new]=raw[new];normal[new]=rn[new];mr[new]=(0,.82,0);bc[new]=1
# UVs for the source head occupy 0..0.94 vertically; the welded neck has its own top strip.
rawh=Image.open(p/'meshy/head_model_v2/texture_urls_0_base_color.png').convert('RGB');head=np.zeros((N,N,3));nmain=round(N*.94);head[N-nmain:]=np.asarray(rawh.resize((N,nmain),Image.Resampling.LANCZOS),float)/255
hn=load(p/'revision_02/head_normal_bake.png');hv=np.array(Image.fromarray(np.uint8(head*255)).convert('HSV'),float)/255
hc=np.zeros((N,N),np.uint8);hc[hcov]=1
mouth=hcov&(abs(hp[...,0]+.00733)<.055)&(hp[...,1]<-.06)&(hp[...,2]>1.513)&(hp[...,2]<1.54)&(hv[...,2]<.28);hc[mouth]=7
teeth=hcov&(hp[...,1]<-.05)&(hp[...,2]>1.515)&(hp[...,2]<1.58)&(head[...,2]>.36)&(hv[...,1]<.5)&(hv[...,2]>.58);hc[teeth]=5
eyes=hcov&(hp[...,1]<-.035)&(hp[...,2]>1.592)&(hp[...,2]<1.632)&(hv[...,0]>.10)&(hv[...,0]<.20)&(hv[...,1]>.5);hc[eyes]=6
assert eyes.sum()>1500 and teeth.sum()>5000,(eyes.sum(),teeth.sum())
neck=(bc==1)&cov&(pos[...,2]>1.32)&(pos[...,2]<1.44)&(abs(pos[...,0])<.16)
headneck=(hc==1)&(hp[...,2]-.4*hp[...,1]<1.535)&(hp[...,2]-.4*hp[...,1]>1.502)&(head.max(-1)>.1)
gain=np.median(base[neck],axis=0)/np.maximum(np.median(head[headneck],axis=0),.02);assert (gain>.4).all() and (gain<2).all(),gain
head[hc==1]=np.clip(head[hc==1]*gain,0,1)
seams=json.loads((p/'revision_02/head_seam_samples.json').read_text());points=np.array([s['pos'] for s in seams]);tree=cKDTree(points)
def sample(a,uv):
 xy=np.clip(np.floor(np.array(uv)*N).astype(int),0,N-1);return a[N-1-xy[:,1],xy[:,0]]
bcols=sample(base,[s['body'] for s in seams])
dist,idx=tree.query(hp[hcov],k=8);w=1/np.maximum(dist,.006)**2;near=(bcols[idx]*w[...,None]).sum(1)/w.sum(1)[:,None]
# Skin colour blends across the real shared neck edge and the separately unwrapped bridge.
skin=(hc[hcov]==1);height=hp[hcov,2]-.4*hp[hcov,1];fade=np.clip((1.545-height)/.05,0,1);fade=fade*fade*(3-2*fade);fade*=skin
head[hcov]=head[hcov]*(1-fade[:,None])+near*fade[:,None]
# The new neck band needs geometry normals, not projected normals from the old source's open cut.
nfade=np.clip((height-1.51)/.025,0,1);hn[hcov]=hn[hcov]*nfade[:,None]+np.array([.5,.5,1])*(1-nfade[:,None])
response={0:(0,1,0),1:(0,.82,0),5:(.4,.43,0),6:(1,.18,0),7:(.2,.75,0)};hm=np.empty((N,N,3))
for k,v in response.items():hm[hc==k]=v
_,(yy,xx)=ndimage.distance_transform_edt(~hcov,return_indices=True)
head=head[yy,xx];hn=hn[yy,xx];hm=hm[yy,xx]
for prefix,b,n,m,c in [('ogr',base,normal,mr,bc),('ogr_head',head,hn,hm,hc)]:
 save(b,t/f'{prefix}_basecolor_1k.png');save(n,t/f'{prefix}_normal_1k.png');save(m,t/f'{prefix}_metal_rough_1k.png');Image.fromarray(c).save(t/f'{prefix}_material_classes.png')
report={'head_skin_gain_rgb':gain.tolist(),'body_new_neck_texels':int(new.sum()),'head_class_texels':{str(k):int((hc==k).sum()) for k in np.unique(hc)},'normal':'Cycles high-to-low bake, flat welded-neck band','head_uv':'Existing layout scaled to v<=0.94; neck bridge v=0.958..0.985','eye_colour':'Preserved gold/yellow and dark pupils from generated head, unchanged by skin grade'}
(p/'revision_02/texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print('REVIEW2_TEXTURES',report)
