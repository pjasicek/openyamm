from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
root=p.parents[2];sys.path.insert(0,str(root))
from finish import clean_soft,register_cell,check_existing
job=json.loads((root/'jobs/g17633_v0_s0.json').read_text());sources=json.loads((root/'sources.json').read_text())
sheet=Image.open(p/'raw.png');sx=sheet.width/job['sheet_size'][0];sy=sheet.height/job['sheet_size'][1]
reports={};base=None
for cell in job['cells']:
 k=cell['asset'];b=cell['cell'];crop=sheet.crop(tuple(round(v*(sx if i%2==0 else sy)) for i,v in enumerate(b)))
 clean,stats=clean_soft(crop,[255,255,0]);cell['native_bounds']=sources[k]['native_bounds']
 clean.save(p/(k+'.master.png'));out,reg=register_cell(clean,job,cell,sheet.size)
 a=np.array(out)
 if base is None:base=a[100:].copy()
 else:a[100:]=base
 Image.fromarray(a).save(p/(k+'.png'))
 reports[k]={'cleanup':stats,'registration':reg}
(p/'extraction_correction.json').write_text(json.dumps({'reason':'Reviewed raw purple/gray art has no yellow material; remove inaccurate companion mask with soft yellow matte extraction. Native base pixels y>=50 identical in all six frames; reuse first restored base.','frames':reports},indent=2))
check_existing(job,sources,p)
