import sys,json,numpy as np
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];T=P/'textures';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
N=1024
load=lambda p:np.asarray(Image.open(p).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
save=lambda a,p:Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def raster(layer):
 d=np.load(P/f'work/uvraster_{layer}.npz');cov=d['piece']>=0;near=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);return d['piece'],d['pos'],cov,near
def padded(a,cov,near):
 out=a[tuple(near)].copy();out[cov]=a[cov];return out
B=load(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png');H=load(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png');pv,pos,cov,near=raster('UVMap');hp,hpos,hcov,hnear=raster('HeadUV')
cls=np.full((N,N),8,np.uint8);skin=np.isin(pv,[9,10])|(np.isin(pv,[3,4])&(pos[...,2]<.596));metal=np.isin(pv,[11,16,67])|(pv>=14);cls[skin]=1;cls[metal]=9
hcls=np.full((N,N),1,np.uint8);hmetal=(hpos[...,2]>1.237)|(hp>=14);hair=(hp==0)&((H.mean(-1)<.37)|(hpos[...,1]>.055)&(hpos[...,2]<1.185));hcls[hair]=2;hcls[hmetal]=9;hcls[np.isin(hp,[12,13])]=6
# The low nape is hair; remove the retexture's brown collar projection there.
patch=(hp==0)&(hpos[...,1]>.055)&(hpos[...,2]<1.185)&(H[...,0]>H[...,1]*1.12);gray=H@np.array([.2126,.7152,.0722]);H[patch]=gray[patch,None]*np.array([.53,.51,.50]);hcls[patch]=2
# Match face and exposed arms gently; preserve the painted facial contrast.
bs=skin&cov;hs=(hcls==1)&hcov&(hpos[...,1]<0)&(hpos[...,2]>1.17);gain=float(np.clip(np.median(B[bs])/max(np.median(H[hs]),.001),.90,1.08));H[(hcls==1)&hcov]*=gain
# Both mapped atlases carry a restrained rest-pose AO grade. Specular uses the current MR red-channel contract.
B*=.80+.20*load(T/'dwa1_ao_1k.png');H*=.80+.20*load(T/'dwa1_head_ao_1k.png');H[hmetal]*=.83;B[metal]*=.92
strength=B[...,1]-np.maximum(B[...,0],B[...,2]);cloth=np.isin(pv,[1,2]);w=np.clip((strength-.003)/.035,0,1)*cloth;w[pv==5]=0
mask=np.zeros((N,N,4));mask[...,0]=ndimage.gaussian_filter(w,.5);mask[...,1]=(pv==5).astype(float);mask=padded(mask,cov,near)
for prefix,base,classes,valid,nr,job in [('dwa1',B,cls,cov,near,'body_retexture_v1'),('dwa1_head',H,hcls,hcov,hnear,'head_retexture_v1')]:
 M=P/'meshy'/job;rough=load(M/'texture_urls_0_roughness.png')[...,0];rough=np.where(classes==9,np.clip(rough,.48,.76),np.clip(rough,.72,.94));spec=np.where(classes==9,.62,np.where(classes==6,.08,.025));ao=load(T/f'{prefix}_ao_1k.png')[...,0];spec*=.65+.35*ao;mr=np.stack([spec,rough,np.where(classes==9,load(M/'texture_urls_0_metallic.png')[...,0],0)],-1)
 for suffix,img in [('basecolor',base),('normal',load(M/'texture_urls_0_normal.png')),('metal_rough',mr)]:save(padded(img,valid,nr),T/f'{prefix}_{suffix}_1k.png')
 Image.fromarray(np.where(valid,classes,0).astype(np.uint8)).save(T/f'{prefix}_material_classes_1k.png')
save(mask,T/'dwa1_region_mask.png');save(np.zeros_like(mask),T/'dwa1_head_region_mask.png')
# Exact original palette indices determine two independent cloth ramps (tunic / trousers).
pals={v:np.frombuffer((ROOT/f'assets_dev/worlds/mm6/textures/pal{k}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for v,k in [('dwa1_a',195),('dwa1_b',196),('dwa1_c',197)]};counts=np.zeros(256);tree=cKDTree(pals['dwa1_a'])
for f in (P.parent/'mm6_dwa1/native').glob('*.png'):
 a=np.array(Image.open(f).convert('RGBA'));rgb=a[a[:,:,3]>0,:3]/255;dist,ids=tree.query(rgb);assert dist.max()<.001;counts+=np.bincount(ids,minlength=256)
base=padded(B,cov,near);lum=R.luminance(base);pal=pals['dwa1_a'];idx=np.arange(256);green=(pal[:,1]>pal[:,0]+.012)&(pal[:,1]>pal[:,2]+.012);ramps={v:[]for v in pals};sources=[]
for channel,selection in enumerate([idx<240,idx>=240]):
 ids=np.where(green&selection&(counts>0)&(R.luminance(pal)>.005))[0];assert len(ids)>=3,ids;order=np.argsort(R.luminance(pal[ids]));ids=ids[order];ys=R.luminance(pal[ids]);weights=counts[ids];cdf=(np.cumsum(weights)-weights*.5)/weights.sum();core=lum[mask[...,channel]>.8];lo,hi=np.percentile(core,[.5,99.5]);stops=np.linspace(lo,hi,16);rank=np.searchsorted(np.sort(core),stops)/len(core)
 for v,palette in pals.items():
  colors=R.srgb_to_linear(palette[ids])*1.3;cols=np.stack([np.interp(rank,cdf,colors[:,c])for c in range(3)],-1);ramps[v].append({'range':[float(lo),float(hi)],'colors':np.clip(cols,0,1).tolist()})
 sources.append({'channel':channel,'palette_indices':ids.tolist(),'core_texels':len(core),'gain_linear':1.3})
RDATA={'variants':list(pals),'materials':[{'base':'Dwarf_A','prefix':'Dwarf','mask':'dwa1_region_mask.png','ramps':ramps},{'base':'DwarfHead_A','prefix':'DwarfHead','mask':'dwa1_head_region_mask.png','ramps':ramps},{'base':'DwarfAxe_A','prefix':'DwarfAxe','mask':'dwa1_head_region_mask.png','ramps':ramps}]};(T/'dwa1_ramps.json').write_text(json.dumps(RDATA,indent=2));report={'palettes':[195,196,197],'regions':sources,'head_skin_gain':gain,'nape_projection_corrected_texels':int(patch.sum()),'MR_red':'specular mask; AO saved separately','steel_constant_between_tiers':True,'classes':{'1':'skin','2':'hair','6':'eyes','8':'cloth/leather','9':'metal','10':'wood'}};(T/'palette_and_material_report.json').write_text(json.dumps(report,indent=2));print(report)
