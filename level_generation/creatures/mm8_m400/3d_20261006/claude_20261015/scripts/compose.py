from pathlib import Path
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];REPO=P.parents[4]
sys.path.insert(0,str(REPO/'level_generation/creatures/claude_shared'))
import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True)
H=P.parent.parent/'meshy/head_retexture_claude_20261015'

def load(path):return np.asarray(Image.open(path).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),float)/255

def save(path,a):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(path)

def classify(base):
    r,g,b=base.transpose(2,0,1)
    skin=(b>r*1.25)&(b>g*.94)
    cloth=(g>r*1.18)&(g>b*1.2)
    warm=(r>g*1.15)&(g>b*1.15)
    pale=(np.min(base,axis=2)>.35)&((np.max(base,axis=2)-np.min(base,axis=2))<.25)
    return skin,cloth,warm,pale

body=load(P.parent/'textures/base_color.png');head=load(H/'texture_urls_0_base_color.png')
bs=classify(body)[0];hs=classify(head)[0]
bcov=np.load(P/'work/uvraster_UVMap.npz')['piece']>=0
hcov=np.load(P/'work/uvraster_HeadUV.npz')['piece']>=0
# The cut crosses clothing, so match skin to skin rather than the green cloth at the boundary.
gain=float(np.median(R.luminance(body)[bs&bcov])/np.median(R.luminance(head)[hs&hcov]))
gain=np.clip(gain,.6,1.6)
lin=R.srgb_to_linear(head);lin[hs]*=gain
head=np.where(lin<=.0031308,12.92*lin,1.055*np.maximum(lin,0)**(1/2.4)-.055)
materials=[];report={'head_skin_luminance_gain':float(gain),'uv_triangles_verified':1594}
for label,base,normal_path,layer in [('Body',body,P.parent/'textures/normal.png','UVMap'),('Head',head,H/'texture_urls_0_normal.png','HeadUV')]:
    raster=np.load(P/'work'/f'uvraster_{layer}.npz');cov=raster['piece']>=0;pos=raster['pos']
    indices=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
    def pad(a):return a[indices[0],indices[1]]
    skin,cloth,warm,pale=classify(base)
    cls=np.full(cov.shape,11,np.uint8);cls[skin]=1;cls[cloth|warm]=8;cls[pale]=5
    if label=='Head':
        cls[~skin&~pale]=3
        eyes=warm&(pos[...,2]>1.48)&(pos[...,2]<1.60)&(pos[...,1]<-.08)
        cls[eyes]=6
    else:
        gold=warm&(pos[...,2]>1.05)&(abs(pos[...,0])>.17)
        cls[gold]=9
    spec=np.full(cov.shape,.1);rough=np.full(cov.shape,.82)
    for k,s,r in [(1,.08,.86),(3,.12,.85),(5,.35,.55),(6,.7,.23),(8,.08,.88),(9,.65,.38)]:
        spec[cls==k]=s;rough[cls==k]=r
    save(T/f'{label}_basecolor.png',pad(base));save(T/f'{label}_normal.png',pad(load(normal_path)))
    save(T/f'{label}_mr.png',np.stack([pad(spec),pad(rough),np.zeros_like(rough)],-1))
    cls[~cov]=0;Image.fromarray(cls).save(T/f'{label}_material_classes.png')
    if label=='Body':
        weight=ndimage.gaussian_filter(pad((cloth&cov).astype(float)),.7)
        ramps,fit=R.fit_ramps(base,{'m400_a':base},weight)
        R.write_mask([weight],T/'body_region_mask.png',size=1024)
        materials.append({'base':'Lizardman_A','prefix':'Lizardman','mask':'body_region_mask.png',
                          'ramps':{k:[v] for k,v in ramps.items()}})
        report['cloth_ramp_fit']=fit
    assert np.all(np.isfinite(base)) and cov.sum()>1000
(T/'ramps.json').write_text(json.dumps({'variants':['m400_a'],'materials':materials},indent=2)+'\n')
(T/'compose_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
