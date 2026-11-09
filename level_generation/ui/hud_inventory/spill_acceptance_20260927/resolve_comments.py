"""Resolve only the captured recent comments; retain reviewed canvases and item alpha."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0,str(HUD))
from repair_spill import comparison


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def border(image, side):
    pixels=np.asarray(image).copy();before=pixels.copy()
    rgb=pixels[:,:,:3].astype(int);chroma=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
    region=np.zeros(chroma.shape,bool)
    if side=='left': region[:,:4]=True
    else: region[-4:,:]=True
    bad=region&(chroma>3)&(pixels[:,:,3]>0)
    # The reported line is painted into RGB. Sample clean pixels inward without
    # removing opacity or changing the portrait/panel dimensions.
    good=~region&(chroma<=3)&(pixels[:,:,3]>=240)
    assert good.any()
    indices=ndimage.distance_transform_edt(~good,return_distances=False,return_indices=True)
    pixels[:,:,:3][bad]=pixels[indices[0],indices[1],:3][bad]
    return Image.fromarray(pixels),dict(method='inspected_border_foreground_extension',side=side,
        band_pixels=4,changed_pixels=int(np.any(pixels!=before,axis=2).sum()))


def inventory(image,native):
    pixels=np.asarray(image).copy();before=pixels.copy();original=np.asarray(native).astype(float)
    xs=[8]+[76+64*i for i in range(13)]+[912]
    ys=[14]+[80+64*i for i in range(8)]+[600]
    target=np.median([original[10+32*y:34+32*y,8+32*x:32+32*x,:3].mean(axis=(0,1))
                      for y in range(9) for x in range(14)],axis=0)
    means=[]
    for row in range(9):
        for col in range(14):
            x,X=xs[col:col+2];y,Y=ys[row:row+2]
            tile=before[y:Y,x:X,:3].astype(float)
            center=tile[7:-7,7:-7].mean(axis=(0,1))
            yy,xx=np.indices(tile.shape[:2]);edge=np.minimum.reduce([xx,yy,tile.shape[1]-1-xx,tile.shape[0]-1-yy])
            weight=np.clip((edge-2)/4,0,1)[:,:,None]
            normalized=target+.40*(tile-center)
            # Retain the existing separator/bevel geometry, at quieter contrast.
            result=tile*.78*(1-weight)+normalized*weight
            pixels[y:Y,x:X,:3]=np.clip(np.rint(result),0,255).astype('uint8')
            means.append(pixels[y+7:Y-7,x+7:X-7,:3].mean(axis=(0,1)))
    return Image.fromarray(pixels),dict(method='native_tone_cell_normalization',columns=14,rows=9,
        geometry='existing tile boundaries retained; color only',native_cell_rgb=target.tolist(),
        texture_contrast=.40,bevel_brightness=.78,cell_mean_std_rgb=np.std(means,axis=0).tolist())


def generated(name,before):
    path=OUT/'generated'/name/'raw.png'
    with Image.open(path) as opened: raw=opened.convert('RGBA')
    if name=='out06':
        result=raw.resize(before.size,Image.Resampling.LANCZOS)
        result.putalpha(before.getchannel('A'))
        return result,dict(method='imagegen_dead_shadowspire_restoration',raw=str(path.relative_to(ROOT)),
                           raw_sha256=sha(path),prompt=str((path.parent/'prompt.txt').relative_to(ROOT)))
    p=np.asarray(raw);a=p[:,:,3]
    bounds=Image.fromarray((a>32).astype('uint8')).getbbox()
    subject=raw.crop(bounds)
    if name=='item263':
        # Preserve the reviewed grip axis and silhouette; align head/collar/shaft
        # bands separately so the new tall master cannot flatten the skull.
        source=np.asarray(subject.convert('RGBa')).astype(float)
        h,w=source.shape[:2];old=np.asarray(before);height,width=old.shape[:2]
        yy=np.interp(np.arange(height),[0,32,65,height-1],[0,180,390,h-1])
        sample=np.zeros((height,width,4),dtype='uint8')
        for y,sy in enumerate(yy):
            src_a=source[min(h-1,round(sy)),:,3]
            sx=np.flatnonzero(src_a>32);dx=np.flatnonzero(old[y,:,3]>32)
            if not len(sx) or not len(dx):continue
            xx=(np.arange(width)-dx[0])*(sx[-1]-sx[0])/max(1,dx[-1]-dx[0])+sx[0]
            for channel in range(4):
                sample[y,:,channel]=np.clip(ndimage.map_coordinates(source[:,:,channel],
                    [np.full(width,sy),xx],order=1,mode='nearest'),0,255)
        aligned=Image.fromarray(sample,'RGBa').convert('RGBA')
    else:
        aligned=subject.convert('RGBa').resize(before.size,Image.Resampling.LANCZOS).convert('RGBA')
    pixels=np.asarray(aligned).copy();source_alpha=pixels[:,:,3].copy()
    # Extend foreground RGB only where the registered alpha needs edge color.
    clean=source_alpha>=128
    indices=ndimage.distance_transform_edt(~clean,return_distances=False,return_indices=True)
    edge=(np.asarray(before)[:,:,3]>0)&(source_alpha<128)
    pixels[:,:,:3][edge]=pixels[indices[0],indices[1],:3][edge]
    pixels[:,:,3]=np.asarray(before)[:,:,3]
    pixels[pixels[:,:,3]==0,:3]=0
    return Image.fromarray(pixels),dict(method='imagegen_material_restoration_registered_to_reviewed_alpha',
        raw=str(path.relative_to(ROOT)),raw_sha256=sha(path),source_alpha_bounds=list(bounds),
        prompt=str((path.parent/'prompt.txt').relative_to(ROOT)),alpha_policy='reviewed fitted alpha retained exactly',
        alignment='head/collar/shaft bands and existing grip axis' if name=='item263' else 'full reviewed canvas')


def main():
    comments=json.loads((OUT/'commented_targets.json').read_text())['records']
    results=[];cache={}
    for comment in comments:
        target=comment['target'];path=ROOT/comment['reviewed'];assert sha(path)==comment['sha256']
        with Image.open(path) as opened:before=opened.convert('RGBA')
        with Image.open(ROOT/comment['native']) as opened:native=opened.convert('RGBA')
        stem=target.split('--')[-1].split('.')[0]
        if stem in ('out06','crysskull','item263'):
            if stem not in cache:cache[stem]=generated(stem,before)
            after,operation=cache[stem]
        elif stem=='fr_inven':after,operation=inventory(before,native)
        else:after,operation=border(before,'left' if 'left' in comment['note'] else 'bottom')
        a,b=np.asarray(before),np.asarray(after);assert a.shape==b.shape and np.array_equal(a[:,:,3],b[:,:,3]),target
        changed=np.any(a!=b,axis=2);assert changed.any(),target
        output=OUT/'resolved'/(target+'.png');output.parent.mkdir(exist_ok=True);after.save(output);output.chmod(0o644)
        proof=OUT/'proofs'/(target+'.jpg');comparison(before,after,changed,proof)
        results.append(dict(**comment,artifact=str(output.relative_to(ROOT)),resolved_sha256=sha(output),
            operation=operation,proof=str(proof.relative_to(ROOT)),changed_rgb_pixels=int(changed.sum()),
            alpha_identical=True,dimensions_identical=True,status='comment_resolved'))
    (OUT/'resolutions.json').write_text(json.dumps(dict(records=results,count=len(results)),indent=2)+'\n')
    print(json.dumps(dict(resolved=len(results),alpha_changes=0,canvas_changes=0),indent=2))


if __name__=='__main__':main()
