"""Genie matte extraction, base normalization and native tonal grade."""
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
    # Pink pixels in narrow finger gaps can be fully opaque after matting.
    # Limit this correction to the immediate vicinity of blue foreground;
    # the intended charcoal-violet vortex is not a blue material.
    c=a[:,:,:3].astype(float);r,g,b=c.transpose(2,0,1)
    blue=(b>r+20)&(g>r+10)&(alpha>0)
    near_blue=ndimage.distance_transform_edt(~blue)<=5
    pink=(np.minimum(r,b)>g+8)&(alpha>0)&near_blue
    a[:,:,0][pink]=np.minimum(r,g+2)[pink].astype(np.uint8)
    return Image.fromarray(a)


def align_late_decay():
    """Register the tiny receding figure separately from its fallen ornaments."""
    root,config,inv=process_family.load('djn')
    name='djndyif0'
    clean=Image.open(ROOT/'cleaned'/f'{name}.png').convert('RGBA')
    original=process_family.native(name,739,inv['logical_canvas'],inv)
    occupied=np.where(np.array(clean)[:,:,3].max(axis=1)>0)[0]
    gap=int(np.argmax(np.diff(occupied)))
    assert occupied[gap+1]-occupied[gap]>10
    split=int((occupied[gap]+occupied[gap+1])//2)
    aligned=Image.new('RGBA',tuple(v*2 for v in inv['logical_canvas']))
    parts=[]
    for label,source_y,target_y in [('receding figure',(0,split),(0,150)),
                                    ('fallen ornaments',(split,clean.height),(150,original.height))]:
        source=clean.crop((0,source_y[0],clean.width,source_y[1]))
        target=original.crop((0,target_y[0],original.width,target_y[1]))
        sb=source.getbbox();tb=target.getbbox();assert sb and tb,label
        tb=(tb[0],tb[1]+target_y[0],tb[2],tb[3]+target_y[0])
        size=(2*(tb[2]-tb[0]),2*(tb[3]-tb[1]))
        patch=source.crop(sb).convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
        aligned.paste(contour(patch,'magenta'),(2*tb[0],2*tb[1]))
        parts.append(dict(part=label,clean_bounds=[sb[0],sb[1]+source_y[0],sb[2],sb[3]+source_y[0]],
                          native_bounds=list(tb),physical_size=list(size)))
    aligned.save(ROOT/'aligned_2x'/f'{name}.png')
    path=ROOT/'registration.json';reg=json.loads(path.read_text())
    reg[name].update(component_registration=parts,canvas_origin_px=[0,0],scale=None,translate=None)
    path.write_text(json.dumps(reg,indent=2)+'\n')


def main():
    from materials import coverage
    process_family.matte.extract=extract
    process_family.fix_contour=contour
    process_family.run('djn')
    align_late_decay()
    for folder in ['cleaned','aligned_2x']:
        for path in (ROOT/folder).glob('*.png'):
            a=np.array(Image.open(path).convert('RGBA'));a[:,:,:3]=np.round(a[:,:,:3].astype(float)*.84).astype(np.uint8)
            im=Image.fromarray(a);im.save(path)
            if folder=='aligned_2x':coverage(im).save(ROOT/'masks_2x'/path.name)
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.84,'status':'fixed native tonal grade; acceptance recorded separately'},indent=2)+'\n')
if __name__=='__main__':main()
