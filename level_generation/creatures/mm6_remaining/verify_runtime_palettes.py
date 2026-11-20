"""Compare installed float lookup/vector math with accepted offline palette previews."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
LUMA=np.array([.2126,.7152,.0722])

def main():
 report=json.loads((HERE/'installation.json').read_text());results=[]
 for package in report['packages']:
  source=REPO/package['source'];root=source.parent;m=json.loads(source.read_text())
  installed=REPO/'assets_dev/engine/sprites_new'/package['package'];runtime=json.loads((installed/'manifest.json').read_text())
  worst=0;tested=0
  for page in m['pages']:
   base=np.array(Image.open(root/page['base']).convert('RGBA'));mask=np.array(Image.open(root/page['mask']).convert('RGBA'))
   # PIL expands R8 to RGB and alpha=255; choose only the contract's channels below.
   indices=np.flatnonzero(base[:,:,3].ravel()>=128)
   if not len(indices):continue
   indices=indices[np.linspace(0,len(indices)-1,min(512,len(indices))).astype(int)]
   original=base.reshape(-1,4)[indices];c=original[:,:3].astype(float)/255
   weights=mask.reshape(-1,4)[indices].astype(float)/255;y=c@LUMA;levels=np.round(y*255).astype(int)
   for palette,v in runtime['variants'].items():
    if v.get('exact_base_bypass'):continue
    model=runtime['recolor_model'];w=weights
    if 'lookup' in v:
     width,height=v['lookup_size'];lut=np.fromfile(installed/v['lookup'],dtype='<f4').reshape(height,width,4)[:,:,:3]
     if model=='masked_native_rgb_displacement_lut_v1':
      cube=lut.reshape(33,33,33,3);coords=np.moveaxis(c*32,-1,0)
      delta=np.stack([ndimage.map_coordinates(cube[:,:,:,k],coords,order=1,mode='nearest') for k in range(3)],-1)
      result=c+w[:,:1]*delta
     elif model=='multi_mask_luminance_lut_v1':result=c*(1-w.sum(1,keepdims=True))+np.einsum('nr,rnc->nc',w,lut[:,levels,:])
     else:result=c*(1-w[:,:1])+lut[0,levels,:]*w[:,:1]
    elif model=='masked_regions_luminance_rgb_v1' or model=='multi_mask_luminance_rgb_v1':
     count=2 if model=='masked_regions_luminance_rgb_v1' else 4;w=w[:,:count]
     result=c*(1-w.sum(1,keepdims=True))+y[:,None]*(w@np.array(v['region_luminance_vectors']))
    else:result=c*(1-w[:,:1])+y[:,None]*np.array(v['luminance_vector'])*w[:,:1]
    expected=np.array(Image.open(root/page['variant_previews'][palette]).convert('RGBA')).reshape(-1,4)[indices]
    out=np.round(np.clip(result,0,1)*255).astype(int)
    error=int(np.abs(out-expected[:,:3].astype(int)).max());worst=max(worst,error);tested+=len(indices)
    assert np.array_equal(original[:,3],expected[:,3])
  results.append(dict(package=package['package'],tested_pixels=tested,max_rgb_byte_error=worst))
  print(package['package'],worst,flush=True)
 (HERE/'runtime_review/palette_math.json').write_text(json.dumps(results,indent=2)+'\n')
 assert max(r['max_rgb_byte_error'] for r in results)<=1, 'Runtime palette operation differs from accepted previews'
 print('All palette contracts agree with accepted previews to <=1 RGB byte')
if __name__=='__main__':main()
