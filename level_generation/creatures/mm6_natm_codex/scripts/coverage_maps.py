import sys,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
P=Path(__file__).resolve().parents[1];tex=Path(sys.argv[1]);folder=tex/'body'
if len(sys.argv)==2:
 label=Image.new('L',(1024,1024));d=ImageDraw.Draw(label)
 for row in json.loads((P/'work/far_uv_faces.json').read_text()):d.polygon([(u*1024,(1-v)*1024)for u,v in row['uv']],fill=255 if row['feather']else 0)
 feather=np.asarray(label)>0;coverage=np.asarray(Image.open(folder/'coverage.png').convert('L'));alpha=np.full((1024,1024),255,np.uint8);alpha[binary_erosion(feather)]=coverage[binary_erosion(feather)];im=Image.open(folder/'0_basecolor.png').convert('RGBA');im.putalpha(Image.fromarray(alpha));im.save(folder/'0_basecolor.png');Image.fromarray(alpha).save(folder/'opacity.png')
else:
 alpha=Image.open(folder/'opacity.png')
 for path in folder.glob('natm_*_body_preview.png'):
  im=Image.open(path).convert('RGBA');im.putalpha(alpha);im.save(path)
