"""MM6 silhouette with imagegen detail restricted to its contact band; isolated native pilot."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from build_land import road_contact,connect,edge
from scipy.ndimage import distance_transform_edt
V=P/'roads_v4'
def compose(n):
 a=np.asarray(Image.open(V/'masks'/f'{n}.png'),float)/255
 base=read(V/'inputs'/f'{n}.png');ai=read(V/'raw'/f'{n}.png',512)
 distance=distance_transform_edt(a>.5)+distance_transform_edt(a<=.5)-1
 band=np.clip((40-distance)/16,0,1)
 ratio=np.clip(seams.linear(ai)/np.maximum(seams.linear(base),.002),.35,3)
 ratio=1+(ratio-1)*band[:,:,None]
 profile=(edge(ratio,'N')+edge(ratio,'S'))/2
 ratio=connect(ratio,dict(N=profile,S=profile,E=np.ones((512,3)),W=np.ones((512,3))))
 delta=seams.linear(base)*(ratio-1)
 rgb=seams.srgb(seams.linear(base)+delta)
 save(V/'reviews'/f'{n}_authoring.png',rgb)
 result=seams.reduce(seams.pad(rgb,'wrap'))
 # Explicit masks/shading use edge gutters; the completed authoring tile is periodic
 # along its open road direction. Crop-based runtime export keeps accepted masters.
 save(V/'reviews'/f'{n}_runtime.png',result)
 np.savez_compressed(V/'layers'/f'{n}.npz',linear_rgb_delta=delta.astype('float32'))
 return result
if __name__=='__main__':compose('7drsrns')
