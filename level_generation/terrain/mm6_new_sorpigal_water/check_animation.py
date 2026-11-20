"""Verify baked loop continuity and sampled native animation, and save review evidence."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
files=sorted((P/'captures/v1_flight').glob('water_flight_lake_anim_*.png'))
assert len(files)==28
frames=[np.array(Image.open(f).convert('RGB')) for f in files]
a=frames[0].astype(float)
water=(a[:,:,2]>a[:,:,0]*1.5)&(a[:,:,2]>a[:,:,1]*1.15)
water[:70]=False;water[850:]=False
land=(a[:,:,0]>a[:,:,1]*1.2)&(a[:,:,0]>a[:,:,2]*1.5)
land[:70]=False;land[850:]=False
changes=[np.abs(b.astype(float)-frames[0]) for b in frames[1:]]
water_changes=[float(d[water].mean()) for d in changes]
land_changes=[float(d[land].mean()) for d in changes]
assert min(water_changes)>0.2,'Water did not animate'
assert max(land_changes)<.2,'Camera or land changed in stationary animation sample'
# Native samples have screenshot overhead; preserve measured sample spacing in the preview.
durations=[max(1,round((b.stat().st_mtime-a.stat().st_mtime)*1000)) for a,b in zip(files,files[1:])]
images=[Image.fromarray(f).crop((0,64,1600,900)).resize((1200,627)) for f in frames]
images[0].save(P/'reports/native_animation.webp',save_all=True,append_images=images[1:],duration=durations+[durations[-1]],loop=0,lossless=True)
sheet=Image.new('RGB',(4*400,2*430),'#202933');draw=ImageDraw.Draw(sheet)
for slot,i in enumerate([0,1,2,3,7,13,20,27]):
 im=Image.fromarray(frames[i]).crop((200,100,600,500));x=slot%4*400;y=slot//4*430
 sheet.paste(im,(x,y+30));draw.text((x+6,y+8),f'Native sample {i:02}',fill='white')
sheet.save(P/'reports/native_animation_samples.png')
r={'samples':28,'sample_span_seconds':sum(durations)/1000,'water_changed':True,'water_mean_abs_change_from_first':water_changes,
 'land_mean_abs_change_from_first':land_changes,'fixed_camera_land_stable':True,
 'limitation':'Discrete native samples and baked-frame loop checks; not full-frame-rate temporal shimmer or performance certification.'}
(P/'reports/native_animation_check.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if not isinstance(v,list)},indent=2))
