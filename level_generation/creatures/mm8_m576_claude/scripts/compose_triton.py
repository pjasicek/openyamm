"""One shared body/head material set with native 577/578/579 colour ramps and padded region masks."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R

def load(path,mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(x,path):Image.fromarray(np.uint8(np.clip(x,0,1)*255+.5)).save(path)
sets={}
for part,layer,material in [('body','UVMap','Triton_A'),('head','HeadUV','TritonHead_A')]:
    N=2048 if part=='body' else 1024
    src=P/'meshy'/f'{part}_retexture_v1';r=np.load(P/'work'/f'uvraster_{layer}.npz');pc,pos=r['piece'],r['pos'];cov=pc>=0
    base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L')
    skin=np.isin(pc,[0,1]);armour=np.isin(pc,[2,3,4,5,6,10,11]);eye=np.isin(pc,[7,8]);gem=pc==9
    cls=np.zeros(pc.shape,np.uint8);cls[skin]=1;cls[armour]=9;cls[eye]=6;cls[gem]=11
    assert np.all(cls[cov]>0),'Unclassified material'
    sets[part]={'base':base,'normal':normal,'rough':rough,'pc':pc,'pos':pos,'cov':cov,'regions':[skin,armour],'classes':cls,'material':material}
# Keep the accepted head grade; the correction is applied to the body below.
head_gain=1.039061487025775
x=R.srgb_to_linear(sets['head']['base']);x[sets['head']['regions'][0]]*=head_gain
sets['head']['base']=np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
for part,v in sets.items():
    pc,cov=v['pc'],v['cov'];cls=v['classes'];idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
    spec=np.zeros(pc.shape);rough=np.zeros(pc.shape)
    for c,(s,r) in {1:(.3,.82),9:(.75,.48),6:(.8,.22),11:(.8,.3)}.items():
        m=cls==c;spec[m]=s;rough[m]=np.clip(r+.12*(v['rough'][m]-np.median(v['rough'][m])),.15,1) if m.any() else []
    orm=np.stack([spec[tuple(idx)],rough[tuple(idx)],np.zeros(pc.shape)],-1)
    v['base']=np.clip(v['base'][tuple(idx)],0,1)
    save(v['base'],T/f'{part}_basecolor.png');save(v['normal'][tuple(idx)],T/f'{part}_normal.png');save(orm,T/f'{part}_orm.png')
    Image.fromarray(cls).save(T/f'{part}_material_classes.png')
    masks=[nd.gaussian_filter(m.astype(float)[tuple(idx)],.45) for m in v['regions']]
    R.write_mask(masks,T/f'{part}_region_mask.png',size=pc.shape[0])
# Freeze the original native-palette ramps so changing body resolution cannot recolour the accepted head.
cfg=json.loads((P/'references_native/material_ramps.json').read_text())
(T/'triton_ramps.json').write_text(json.dumps(cfg,indent=2))
# The body return has much brighter scale crowns than the separately painted head.
# Match the skin tone distribution, keeping the native ramps and armour grade fixed.
body,head=sets['body'],sets['head']
bl=R.luminance(body['base']);hl=R.luminance(head['base'])
quantiles=[0,2,10,25,50,75,90,98,100]
source=np.percentile(bl[body['regions'][0]],quantiles)
neck=head['regions'][0]&(head['pos'][:,:,2]<1.50)
target=np.percentile(hl[neck],quantiles)
assert np.all(np.diff(source)>0) and np.all(np.diff(target)>0)
matched=np.interp(bl,source,target)
linear=R.srgb_to_linear(body['base'])
mask=body['regions'][0]
linear[mask]*=(matched[mask]/np.maximum(bl[mask],1e-6))[:,None]
graded=np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
idx=nd.distance_transform_edt(~body['cov'],return_distances=False,return_indices=True)
save(graded[tuple(idx)],T/'body_basecolor.png')
assert np.allclose(R.luminance(graded)[mask],matched[mask],atol=1e-6)
(T/'texture_report.json').write_text(json.dumps({'head_luminance_gain':head_gain,'palette_ids':[577,578,579],'ramp_linear_gain':1.35,'orm':'R specular mask; G roughness; B zero','body_size':2048,'head_size':1024,'body_skin_match':{'reference':'accepted lower head/neck skin below rest Z=1.50 m','quantiles':quantiles,'source':source.tolist(),'target':target.tolist()}},indent=2))
# The prop uses the original isolated painting with padded transparent texels; projection coordinates stay unchanged.
D=T/'props';D.mkdir(exist_ok=True);raw=Image.open(P/'references_props/trident.png').convert('RGBA').resize((512,1024),Image.Resampling.LANCZOS)
a=np.asarray(raw);cov=a[:,:,3]>128;idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True);rgb=a[:,:,:3][tuple(idx)]/255
save(rgb,D/'trident_basecolor.png');normal=np.empty_like(rgb);normal[:]=[.5,.5,1];save(normal,D/'trident_normal.png')
hsv=np.asarray(Image.fromarray(np.uint8(rgb*255)).convert('HSV'),float)/255;steel=(hsv[:,:,2]>.22)&~((hsv[:,:,0]>.60)&(hsv[:,:,0]<.82)&(hsv[:,:,1]>.4))
orm=np.zeros_like(rgb);orm[:,:,0]=np.where(steel,.8,.3);orm[:,:,1]=np.where(steel,.48,.77);save(orm,D/'trident_orm.png')
print('TEXTURE COMPOSE: matched body skin to accepted head; body 2K, head 1K')
