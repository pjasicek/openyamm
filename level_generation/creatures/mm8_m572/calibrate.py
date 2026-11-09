"""Shared batch registration against native warm body landmarks, without per-pose fitting."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.optimize import minimize
from process import ROOT, queue, save, fix

def body(im):
    a = np.asarray(im.resize((128,128),Image.Resampling.BILINEAR)).astype(float)
    r,g,b = np.moveaxis(a[:,:,:3],-1,0)
    coverage = np.clip((r-g+4)/12,0,1)*np.clip((g-b)/12,0,1)*a[:,:,3]/255
    coverage *= np.clip(ndi.distance_transform_edt(a[:,:,3]>200)/2,0,1)
    return ndi.gaussian_filter(coverage,1)

def warp(a, values):
    scale, dx, dy = values
    offset = 64-(64+np.array([dy,dx]))/scale
    return ndi.affine_transform(a,np.eye(2)/scale,offset=offset,order=1,mode='constant')

def run():
    reg=json.loads((ROOT/'registration.json').read_text())
    batches=json.loads((ROOT/'batches.json').read_text())
    results={};finalReg={}
    (ROOT/'registered_2x').mkdir(exist_ok=True)
    (ROOT/'review/registration').mkdir(exist_ok=True,parents=True)
    for key,batch in batches.items():
        names=batch['frames']
        if any(n not in reg for n in names):continue
        art=[];native=[]
        for n in names:
            canvas=Image.new('RGBA',(576,576));canvas.paste(Image.open(ROOT/f'aligned_2x/{n}.png'),tuple(32+v for v in reg[n]['canvas_origin_px']));art.append(canvas)
            canvas=Image.new('RGBA',(576,576));canvas.paste(queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),(32,32));native.append(canvas)
        generated=[body(im) for im in art];targets=[body(im) for im in native]
        def objective(values):
            numerator=denominator=0
            for a,b in zip(generated,targets):
                w=warp(a,values);numerator+=2*(w*b).sum();denominator+=(w*w+b*b).sum()
            return 1-numerator/max(denominator,1e-6)+.02*(values[0]-1)**2
        values=batch.get('accepted_calibration')
        if values is None:values=[1.,0.,0.] if key=='identity' else minimize(objective,[1,0,0],method='Powell',
            bounds=[(.70,1.08),(-15,15),(-15,15)],options={'maxiter':40,'xtol':.0005}).x.tolist()
        scale,dx,dy=values
        results[key]={'scale':scale,'translation_2x_px':[4.5*dx,4.5*dy],
                      'objective_before':objective([1,0,0]),'objective_after':objective(values),
                      'frames':names,'status':'needs_visual_review'}
        sheet=Image.new('RGB',(256*len(names),840),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,(name,im,source,mask,target) in enumerate(zip(names,art,native,generated,targets)):
            # Shared similarity transform for the entire sheet, never an individual silhouette fit.
            offsetX=288-(288+4.5*dx)/scale;offsetY=288-(288+4.5*dy)/scale
            out=fix(im.convert('RGBa').transform((576,576),Image.Transform.AFFINE,
                (1/scale,0,offsetX,0,1/scale,offsetY),Image.Resampling.BICUBIC).convert('RGBA'))
            out.save(ROOT/f'registered_2x/{name}.png')
            box=out.getchannel('A').getbbox();assert box[0]>3 and box[1]>3 and box[2]<573 and box[3]<573,(name,box)
            finalReg[name]={**reg[name],'canvas_origin_px':[-32,-32],'aligned_size_px':[576,576],'calibration':results[key]}
            overlay=np.zeros((128,128,3),np.uint8)
            overlay[:,:,0]=np.round(target*255).clip(0,255).astype(np.uint8)
            overlay[:,:,1]=np.round(warp(mask,values)*255).clip(0,255).astype(np.uint8)
            for row,pic in enumerate([source,out,Image.fromarray(overlay).resize((512,512))]):
                bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic.convert('RGBA'))
                sheet.paste(bg.resize((256,256)).convert('RGB'),(256*i,280*row+24))
                draw.text((256*i+4,280*row+4),name+' '+['native','registered','native red/art green'][row],fill='white')
        sheet.save(ROOT/f'review/registration/{key}.png')
        print(key,round(scale,3),[round(dx*4.5,1),round(dy*4.5,1)],flush=True)
    save(ROOT/'calibration_registration.json',finalReg)
    save(ROOT/'calibration.json',{'method':'One uniform scale and translation per generated action/view batch '
         'against warm body landmarks over all poses together. No rotation, independent recentering, equal-height '
         'normalization, source silhouette replacement or per-frame fit. Identity fixed at accepted layout.',
         'landmarks':'Soft warm flame/body and orange feather coverage; eroded alpha excludes thin flame/foot tips. '
         'Every overlap contact requires visual review; RGB classifier alone cannot validate anatomy.',
         'batches':results})

if __name__=='__main__':run()
