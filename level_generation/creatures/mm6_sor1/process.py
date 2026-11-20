"""Purple-safe matte extraction and fixed native-tonal grade for MM6 sorcerer."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family


def extract(rgb):
    c=np.array(rgb,dtype=float)/255
    dominance=np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]
    # Opaque purple robe has moderate magenta dominance; the flat key is near 1.
    core=(dominance<.03)|(ndimage.distance_transform_edt(dominance<.5)>3)
    background=(dominance>.82)&(c[:,:,0]>.9)&(c[:,:,2]>.9)
    distance,idx=ndimage.distance_transform_edt(~core,return_indices=True)
    _,bi=ndimage.distance_transform_edt(~background,return_indices=True)
    f=c[idx[0],idx[1]];b=c[bi[0],bi[1]];v=f-b
    alpha=np.clip(((c-b)*v).sum(axis=2)/np.maximum((v*v).sum(axis=2),1e-8),0,1)
    alpha[core]=1;alpha[(distance>7)|background]=0
    restored=(c-(1-alpha[:,:,None])*b)/np.maximum(alpha[:,:,None],1/255)
    # Project edge chroma onto nearby real foreground; preserve interior purple.
    limit=np.minimum(f[:,:,0],f[:,:,2])-f[:,:,1]+2/255
    excess=np.maximum(0,np.minimum(restored[:,:,0],restored[:,:,2])-restored[:,:,1]-limit)
    restored[:,:,0]-=excess;restored[:,:,2]-=excess
    restored=np.clip(restored,0,1);restored[core]=c[core];restored[alpha==0]=0
    return Image.fromarray(np.round(np.dstack([restored,alpha])*255).astype(np.uint8)),dict(method='purple-safe local matte projection',core_threshold=.35)


def contour(im,matte):
    a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
    inside=ndimage.distance_transform_edt(alpha>=250)>3
    if not inside.any():return im
    dist,idx=ndimage.distance_transform_edt(~inside,return_indices=True)
    f=c[idx[0],idx[1]];limit=np.minimum(f[:,:,0],f[:,:,2])-f[:,:,1]+2
    edge=(alpha>0)&~inside&(dist<=5)
    excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-limit)*edge
    c[:,:,0]-=excess;c[:,:,2]-=excess
    green_limit=f[:,:,1]-np.maximum(f[:,:,0],f[:,:,2])+2
    green_excess=np.maximum(0,c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2])-green_limit)*edge
    c[:,:,1]-=green_excess
    a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8)
    return Image.fromarray(a)


def main():
    process_family.matte.extract=extract
    process_family.fix_contour=contour
    process_family.run('sor1')
    for folder in ['cleaned','aligned_2x']:
        for path in (ROOT/folder).glob('*.png'):
            a=np.array(Image.open(path).convert('RGBA'))
            c=a[:,:,:3].astype(float)
            # Warm pink contamination on skin is distinct from intentional B>R purple cloth.
            warm=c[:,:,0]>=c[:,:,2]-2
            excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-8)*warm
            c[:,:,0]-=excess;c[:,:,2]-=excess
            a[:,:,:3]=np.round(np.clip(c,0,255)*.82).astype(np.uint8)
            Image.fromarray(a).save(path)
    from landmarks import refine
    refine()
    (ROOT/'tone.json').write_text(json.dumps(dict(rgb_gain=.82,matte_core_threshold=.35,
        note='Purple robe is intentional. Generic magenta-excess audit will flag legitimate purple edges; inspect recorded edge contacts.'),indent=2)+'\n')

if __name__=='__main__':main()
