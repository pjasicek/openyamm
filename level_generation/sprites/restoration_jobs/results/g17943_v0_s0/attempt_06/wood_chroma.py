from pathlib import Path
import json,numpy as np
from PIL import Image
p=Path(__file__).resolve().parent;k=next(iter(json.loads((p/'checks.json').read_text())['frames']))
a=np.array(Image.open(p/f'{k}.png').convert('RGBA'));Image.fromarray(a).save(p/f'{k}.before_wood_chroma.png')
rgb=a[:,:,:3].astype(float);lum=(rgb*np.array([.2126,.7152,.0722])).sum(2,keepdims=True)
a[:,:,:3]=np.clip(np.rint(lum+.35*(rgb-lum)),0,255).astype(np.uint8)
Image.fromarray(a).save(p/f'{k}.png')
