import sys
import numpy as np
from PIL import Image
sys.path.insert(0,'scripts')
import project_lib as PL
Image.MAX_IMAGE_PIXELS=None
F=np.load('work/faces.npz'); nb=(F['head']==0)&(F['torso']==0)
pos,_,cov,_,_=PL.raster(F['uvb'][nb],F['co'][nb],2048)
a=np.asarray(Image.open('textures/zombie_final_old2k.png').convert('RGB'),np.float32)
g=np.asarray(Image.open('textures/zombie_basecolor_graded.png').convert('RGB'),np.float32)
for nm,c,r in (('kneeL',(0.227,-0.09,-0.26),0.05),('kneeR',(-0.227,-0.09,-0.26),0.05),('forearmL',(0.5,-0.1,0.7),0.05),('thighL',(0.15,-0.08,0),0.05),('shinL',(0.3,-0.04,-0.45),0.05)):
    m=cov&(np.linalg.norm(pos-np.array(c),axis=2)<r)
    print(nm,int(m.sum()),'graded',g[m].mean(0).round(0),'final',a[m].mean(0).round(0),'p90',np.percentile(a[m].mean(1),90).round(0))
