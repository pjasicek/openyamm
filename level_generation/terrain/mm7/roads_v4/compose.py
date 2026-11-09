"""Import generated road contact bands and continue finished artwork through shared openings."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from scipy.ndimage import distance_transform_edt,gaussian_filter,binary_fill_holes,label,binary_closing,binary_dilation
from roads_v5.collars import graft
V=P/'roads_v4'

def main():
 sources=json.loads((V/'mask_sources.json').read_text());fields={}
 for n,r in sources.items():
  source=np.load(V/'fields'/f'{n}.npz');a=source['coverage'].astype(float);shade=source['shade'].astype(float)
  base=seams.srgb(seams.linear(read(M/'materials/dirt.png'))*(1-a[:,:,None])+seams.linear(read(M/'materials/roads.png'))*a[:,:,None])*shade[:,:,None]
  ai=read(V/'raw'/f'{n}.png',512)
  distance=distance_transform_edt(a>.5)+distance_transform_edt(a<=.5)-1
  band=np.clip((40-distance)/16,0,1)
  # Use the accepted dirt even where the AI rounds an edge inward. Importing
  # generated earth there would leave a coloured halo inside the original mask.
  stone=(ai[:,:,0]-ai[:,:,2])/np.maximum(ai.mean(2),1)<.32
  yy,xx=np.mgrid[-6:7,-6:7];disk=xx*xx+yy*yy<=36
  stone=binary_closing(np.pad(stone,16,mode='edge'),structure=disk)[16:-16,16:-16]
  stone=binary_fill_holes(stone);components,_=label(stone)
  sizes=np.bincount(components.ravel());sizes[0]=0;stone=components==sizes.argmax()
  stone=binary_dilation(stone,iterations=3)
  stone &= distance_transform_edt(a<=.5)<=12
  dirt=read(M/'materials/dirt.png')
  earth=np.clip(gaussian_filter(seams.linear(ai).mean(2)/np.maximum(seams.linear(dirt).mean(2),.002),2),.5,1)
  target=np.where(stone[:,:,None],ai,seams.srgb(seams.linear(dirt)*earth[:,:,None]))
  ratio=np.clip(seams.linear(target)/np.maximum(seams.linear(base),.002),.05,32)
  ratio=1+(ratio-1)*band[:,:,None]
  fields[n]=dict(alpha=a,shade=shade,base=base,ratio=ratio,band=band,topology=r['topology'])
 images={n:seams.srgb(seams.linear(f['base'])*f['ratio']) for n,f in fields.items()}
 images=graft(images,fields,read(M/'materials/dirt.png'))
 report={}
 for n,f in fields.items():
  rgb=images[n]
  ratio=seams.linear(rgb)/np.maximum(seams.linear(f['base']),.00001)
  delta=seams.linear(rgb)-seams.linear(f['base'])
  save(V/'reviews'/f'{n}_authoring.png',rgb)
  a=seams.pad(f['alpha'],'edge')[:,:,None]
  padded_base=seams.srgb(seams.linear(seams.pad(read(M/'materials/dirt.png'),'wrap'))*(1-a)+seams.linear(seams.pad(read(M/'materials/roads.png'),'wrap'))*a)*seams.pad(f['shade'],'edge')[:,:,None]
  padded_rgb=seams.srgb(seams.linear(padded_base)*seams.pad(ratio,'edge'))
  save(V/'reviews'/f'{n}_runtime.png',seams.reduce(padded_rgb))
  np.savez_compressed(V/'layers'/f'{n}.npz',linear_rgb_delta=delta.astype('float32'))
  report[n]=dict(input_sha256=sha(V/'inputs'/f'{n}.png'),raw_sha256=sha(V/'raw'/f'{n}.png'),mask_sha256=sha(V/'masks'/f'{n}.png'),layer_sha256=sha(V/'layers'/f'{n}.npz'))
 (V/'build.json').write_text(json.dumps(dict(method='Accepted MM6 silhouettes, MM7-only diagonal routes, imagegen contact bands with paired finished-art donor collars at shared openings; masters untouched.',files=report),indent=2)+'\n')
 print('Composed',len(fields),'roads')
if __name__=='__main__':main()
