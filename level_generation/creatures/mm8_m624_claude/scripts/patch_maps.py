from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image
P=Path(__file__).resolve().parents[1];d=np.load(P/'work/body_missing_uv.npz');uv=d['source_uv'];out=d['output_pixels'];target=P/'texturing/body_maps';target.mkdir(exist_ok=True)
for src in (P/'meshy/body_retexture_v1').glob('texture_urls_0_*.png'):
 a=np.asarray(Image.open(src).convert('RGB').resize((2048,2048)));canvas=np.empty((2176,2048,3),np.uint8);canvas[128:]=a;canvas[:128]=a[0]
 sampled=np.stack([map_coordinates(a[...,c].astype(float),[(1-uv[:,1])*2048-.5,uv[:,0]*2048-.5],order=1,mode='nearest')for c in range(3)],1)
 if 'normal' in src.name:sampled[:]=[128,128,255]
 canvas[out[:,0],out[:,1]]=np.clip(sampled,0,255).astype(np.uint8);Image.fromarray(canvas).save(target/src.name)
print('BAKED 12 omitted faces into a 128-pixel atlas strip; original source maps preserved.')
