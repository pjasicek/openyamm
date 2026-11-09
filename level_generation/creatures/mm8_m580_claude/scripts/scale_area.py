from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,math
P=Path('level_generation/creatures/mm8_m580_claude');d=np.load(P/'work/scale_samples.npz');model=[];native=[];bb=[]
for i,co in enumerate(d['co']):
 pts=co[:,[0,2]];lo=pts.min(0);hi=pts.max(0);px=(pts-lo)*1200;image=Image.new('1',tuple(np.ceil((hi-lo)*1200+3).astype(int)));draw=ImageDraw.Draw(image)
 for tri in d['tri']:draw.polygon([tuple(x) for x in px[tri]],fill=1)
 model.append(float(np.asarray(image).sum()/1200**2));bb.append((hi-lo).tolist())
 f=Path('assets_dev/engine/sprites')/f'm580w{chr(97+i)}0.bmp';a=np.asarray(Image.open(f));assert a.ndim==2;native.append(int((a!=0).sum()))
scale=math.sqrt(np.mean(native)*16/np.mean(model));report={'native_front_walk_pixel_areas':native,'native_sft_scale':4,'model_front_idle_areas':model,'model_front_idle_bounds_xz':bb,'equal_mean_silhouette_area_scale':scale,'installed_scale':650.,'installed_area_ratio_to_native':650**2/(scale**2),'decision':'Retain 650 for all tiers if mean projected area differs by under 10%; preserves the roughly 940-world-unit native side length.'};assert abs(report['installed_area_ratio_to_native']-1)<.1,report
(P/'review/scale_calibration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
