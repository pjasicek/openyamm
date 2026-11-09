import numpy as np
from PIL import Image
def hsv(rgb):
    mx,mn=rgb.max(-1),rgb.min(-1); sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0); r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    return np.degrees(np.arctan2(np.sqrt(3)*(g-b),2*r-g-b))%360,sat,mx
def classes(a):
    h,s,v=hsv(a)
    hide=(h>42)&(h<150)&(s>.30)
    lea=((h<34)|(h>345))&(s>.42)&(v>.2)
    steel=(s<.22)
    return hide,steel,lea,h,s,v
if __name__=='__main__':
    m=np.asarray(Image.open('source/raw/skins/lizardorc.png').convert('RGB'),np.float32)/255
    for nm,a in (('MM9',m),('body',np.asarray(Image.open('textures/body_basecolor_graded.png').convert('RGB'),np.float32)/255),('head',np.asarray(Image.open('textures/head_basecolor_graded.png').convert('RGB'),np.float32)/255),('bodyraw',np.asarray(Image.open('textures/body_basecolor.png').convert('RGB'),np.float32)/255)):
        hi,st,le,h,s,v=classes(a)
        for k,mk in (('hide',hi),('steel',st),('leather',le)):
            q=a[mk]; print(nm,k,'share',round(mk.mean(),3),'mean',np.round(q.mean(0)*255).astype(int),'p10/50/90 V',np.round(np.percentile(v[mk],[10,50,90])*255).astype(int),'sat',round(float(s[mk].mean()),2))
