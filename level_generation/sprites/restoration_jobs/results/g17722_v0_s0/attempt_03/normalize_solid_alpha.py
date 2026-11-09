from pathlib import Path
from PIL import Image
import numpy as np
import json
p=Path(__file__).resolve().parent
for k in json.loads((p/'checks.json').read_text())['frames']:
 f=p/(k+'.png');b=p/(k+'.before_alpha.png')
 if not b.exists():b.write_bytes(f.read_bytes())
 a=np.array(Image.open(b).convert('RGBA'))
 a[:,:,3]=np.rint(np.clip(a[:,:,3].astype(float)*255/250,0,255)).astype('uint8')
 a[a[:,:,3]==0,:3]=0
 Image.fromarray(a).save(f)
