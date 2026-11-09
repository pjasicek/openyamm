"""Fit repainted endpoints with a screened harmonic correction to clean road borders."""
import sys,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.fft import dstn,idstn
from scipy.ndimage import distance_transform_edt
for folder in ['runtime','masks']:
 (HERE/folder).mkdir(exist_ok=True)
 for f in (HERE.parent/'v7'/folder).glob('*.png'):shutil.copy2(f,HERE/folder/f.name)
b=json.loads((HERE.parent/'v9/build.json').read_text())
for r in b['tiles']:
 r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
for r in b['tiles']:
 n=r['name']
 if n[4:] not in ['ne1','ne2','nw1','nw2']:continue
 shutil.copy2(HERE.parent/'v8/masks'/(n+'.png'),HERE/'masks'/(n+'.png'))
 gen=read(HERE/'raw'/('drsr'+n[4:]+'.png'),256)
 base=read(HERE/'inputs'/(n+'.png'))
 alpha=read(HERE.parent/'v8/masks'/(n+'.png'),256)[:,:,0]/255
 coverage=np.clip((distance_transform_edt(alpha>.5)-.5)/1.5,0,1)*alpha
 im=base+(gen-base)*coverage[:,:,None]
 target=read(HERE.parent/'v7/runtime'/(n+'.png'))
 delta=np.zeros_like(im);delta[0]=target[0]-im[0];delta[-1]=target[-1]-im[-1];delta[:,0]=target[:,0]-im[:,0];delta[:,-1]=target[:,-1]-im[:,-1]
 rhs=np.zeros((254,254,3));rhs[0]+=delta[0,1:-1];rhs[-1]+=delta[-1,1:-1];rhs[:,0]+=delta[1:-1,0];rhs[:,-1]+=delta[1:-1,-1]
 k=np.arange(1,255);e=2-2*np.cos(np.pi*k/255);den=e[:,None]+e[None,:]+.04
 delta[1:-1,1:-1]=idstn(dstn(rhs,type=1,axes=(0,1),norm='ortho')/den[:,:,None],type=1,axes=(0,1),norm='ortho')
 im+=delta
 save(HERE/'runtime'/(n+'.png'),im)
 r['runtime_sha256']=sha(HERE/'runtime'/(n+'.png'))
b['method']='Clean v7 non-diagonal roads restored; AI endpoint repair with screened harmonic boundary fit on native-shape diagonals.'
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
