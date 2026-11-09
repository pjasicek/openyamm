"""Insert only the diagonal half of the generated shared junction repair."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.fft import dstn,idstn
patch=np.asarray(Image.open(HERE/'raw/exact_join.png').convert('RGB').resize((96,176),Image.LANCZOS),float)[:,:48]
for n in ['drsrne2','gdrdne2']:
 im=read(HERE/'runtime'/(n+'.png'));original=im[48:224,208:256].copy()
 alpha=read(HERE/'masks'/(n+'.png'),256)[48:224,208:256,0]/255
 source=original+(patch-original)*alpha[:,:,None]
 delta=np.zeros_like(source);delta[0]=original[0]-source[0];delta[-1]=original[-1]-source[-1];delta[:,0]=original[:,0]-source[:,0];delta[:,-1]=original[:,-1]-source[:,-1]
 height,width=source.shape[:2];rhs=np.zeros((height-2,width-2,3))
 rhs[0]+=delta[0,1:-1];rhs[-1]+=delta[-1,1:-1];rhs[:,0]+=delta[1:-1,0];rhs[:,-1]+=delta[1:-1,-1]
 yy=np.arange(1,height-1);xx=np.arange(1,width-1)
 den=(2-2*np.cos(np.pi*yy/(height-1)))[:,None]+(2-2*np.cos(np.pi*xx/(width-1)))[None,:]
 delta[1:-1,1:-1]=idstn(dstn(rhs,type=1,axes=(0,1),norm='ortho')/den[:,:,None],type=1,axes=(0,1),norm='ortho')
 result=source+delta
 # Explicitly preserve all patch boundary pixels and non-road terrain.
 result=original+(result-original)*alpha[:,:,None]
 result[0]=original[0];result[-1]=original[-1];result[:,0]=original[:,0];result[:,-1]=original[:,-1]
 im[48:224,208:256]=result;save(HERE/'runtime'/(n+'.png'),im)
b=json.loads((HERE/'build.json').read_text())
for r in b['tiles']:r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
b['exact_join']='Generated shared crop; only diagonal half inserted, straight side and every boundary pixel retained'
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
