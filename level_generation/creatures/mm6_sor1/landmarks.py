"""Native landmarks guide local enhanced-art selections; no resized native mask is shipped."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parent

def refine():
    inv=json.loads((ROOT/'sources.json').read_text());reg=json.loads((ROOT/'registration.json').read_text())
    records={};repo=ROOT.parents[2];canvas=inv['logical_canvas']
    for n,s in inv['sources'].items():
        path=ROOT/'aligned_2x'/f'{n}.png';im=Image.open(path).convert('RGBA');a=np.array(im);w=np.array(Image.open(ROOT/'masks_2x'/f'{n}.png'))
        native=Image.open(repo/s['path']);idx=np.array(native);offset=np.array([(canvas[0]-native.width)//2,canvas[1]-native.height])
        origin=np.array(reg[n]['canvas_origin_px']);records[n]={}
        for kind,selection in [('chest',np.isin(idx,[10,11,13,14,15,16,17,18,19,20,21,22,23])),('cap',np.isin(idx,[3,4,5,6,7,8,9,12]))]:
            ny=np.indices(idx.shape)[0]
            if kind=='chest':selection &= ny<idx.shape[0]*.48
            elif n.startswith('sor1at'):selection &= ny>idx.shape[0]*.65
            labels,k=ndimage.label(selection);sizes=np.bincount(labels.ravel());sizes[0]=0
            if not sizes.max():continue
            component=labels==sizes.argmax();ys,xs=np.where(component)
            # Expand local bounds only; enhanced hue/component determines coverage.
            x0,y0=(np.array([xs.min(),ys.min()])+offset)*2-origin
            x1,y1=(np.array([xs.max()+1,ys.max()+1])+offset)*2-origin
            if kind=='chest':
                # Native insert is triangle within gold V, enhanced purple is separated by gold.
                cx=(x0+x1)/2;cy=(y0+y1)/2
                core=w[:,:,0]>180;labels,k=ndimage.label(core)
                candidates=[]
                for lab in np.unique(labels[max(0,y0):min(im.height,y1),max(0,x0):min(im.width,x1)]):
                    if lab==0:continue
                    yy,xx=np.where(labels==lab)
                    if len(xx)>max(100,(x1-x0)*(y1-y0)*3):continue
                    if yy.max()-yy.min()>max(20,(y1-y0)*1.7):continue
                    score=((xx.mean()-cx)/max(8,x1-x0))**2+((yy.mean()-cy)/max(8,y1-y0))**2
                    candidates.append((score,int(lab)))
                if candidates:
                    score,lab=min(candidates)
                    if score<1:
                        chosen=ndimage.binary_dilation(labels==lab,iterations=1)&(w[:,:,0]>0)
                        w[:,:,0][chosen]=0
                        records[n][kind]=dict(native_box=[int(x0),int(y0),int(x1),int(y1)],selected_pixels=int(chosen.sum()))
            else:
                yy,xx=np.indices(a.shape[:2]);cx=(x0+x1)/2;cy=(y0+y1)/2
                # Round orange foot cap, gold shaft remains outside this small guide.
                radx=max(7,(x1-x0)*.8);rady=max(7,(y1-y0)*.8)
                region=((xx-cx)/radx)**2+((yy-cy)/rady)**2<1
                rgb=a[:,:,:3].astype(float)/255;r,g,b=rgb.transpose(2,0,1)
                warm=(r>g*1.2)&(g>b*1.2)&(a[:,:,3]>0)
                chosen=region&warm
                w[:,:,1][chosen]=255;w[:,:,0][chosen]=0
                records[n][kind]=dict(native_box=[int(x0),int(y0),int(x1),int(y1)],selected_pixels=int(chosen.sum()))
        Image.fromarray(w,'RGBA').save(ROOT/'masks_2x'/f'{n}.png')
    (ROOT/'landmark_selections.json').write_text(json.dumps(records,indent=2)+'\n')
