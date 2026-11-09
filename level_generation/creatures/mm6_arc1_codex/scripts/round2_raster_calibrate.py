import json
from pathlib import Path
P=Path(__file__).resolve().parents[1];code=(P/'scripts/round2_distance_fit.py').read_text();exec(code[:code.index('faces=[raster')]);records=[]
reference=np.stack([np.array(Image.open(D/f'body_l3_factor0_{i}.png'))[:,:,3]>=128 for i in range(8)]).ravel()
for dx in [-.5,-.25,0,.25,.5]:
 for dy in [-.5,-.25,0,.25,.5]:
  cover[:]=0;hits[:]=0
  for t in tri:cover[raster(proj[:,t]+np.array([dx,dy])*SS)]+=1
  np.add.at(hits,parent(np.flatnonzero(cover)),1);mask=hits>=SS*SS/2;score=float((mask&reference).sum()/(mask|reference).sum());records.append({'x':dx,'y':dy,'iou':score});print('RASTER',dx,dy,score,flush=True)
(D/'raster_calibration.json').write_text(json.dumps(records,indent=2))
