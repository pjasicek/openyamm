import sys, json
import numpy as np
from pathlib import Path
from PIL import Image
sys.path.insert(0,'../claude_shared'); sys.path.insert(0,'scripts')
import tier_textures as TT
import importlib.util
src=open('scripts/seam_fix.py').read().split('for t in \'abc\':')[0]
exec(src)
for t in 'ab':
    im=np.asarray(Image.open(T/f'thrall_torso_{t}_final.png').convert('RGB'),np.float32)/255
    L=np.clip(TT.apply(base,mask,e['ramps'][f'thrall_{t}']),0,1)
    o,f=Z['Lu'],Z['Lf']; u=(f-o)/np.linalg.norm(f-o)
    st=(PT-o)@u; sl=(PL-o)@u
    st_ok=CT&(PT[...,0]>0); sl_ok=CL&(PL[...,0]>0)
    for a in np.arange(-0.02,0.16,0.02):
        mt=st_ok&(st>=a)&(st<a+.02)&(PT[...,1]>-.25); ml=sl_ok&(sl>=a)&(sl<a+.02)
        print(t,round(float(a),2),'T',np.round(np.median(im[mt],axis=0),2) if mt.sum()>50 else None,int(mt.sum()),'L',np.round(np.median(L[ml],axis=0),2) if ml.sum()>50 else None,int(ml.sum()), 'maskR', round(float(mask[...,0][ml].mean()),2) if ml.sum()>50 else None)
