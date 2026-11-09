"""Author deterministic broad mineral swatches; geometry supplies the crystal facets."""
from pathlib import Path
import numpy as np
from PIL import Image

p=Path(__file__).resolve().parents[1]/'textures'
p.mkdir(exist_ok=True)
y,x=np.mgrid[:2048,:2048];u=(x%256)/256;v=(y%256)/256;tile=(y//256)*8+x//256
rng=np.random.default_rng(596);shade=rng.uniform(.62,1.32,64);shade[::9]=1.65
cloud=.96+.035*np.sin(u*16+v*10)+.025*np.sin(u*36-v*18)+.018*np.cos(u*67+v*52)
base=np.array([.62,.36,.49]);rgb=np.clip(base*shade[tile,None]*cloud[:,:,None],30/255,243/255)
assert rgb.shape==(2048,2048,3) and np.isfinite(rgb).all()
Image.fromarray((rgb*255).astype(np.uint8),'RGB').save(p/'crystal_basecolor.png')
Image.new('L',(1024,1024),11).save(p/'crystal_material_classes.png')
