from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
root=p.parents[2];sys.path.insert(0,str(root))
from finish import clean_soft,register_cell,check_existing
job=json.loads((root/'jobs/g17677_v0_s0.json').read_text());sources=json.loads((root/'sources.json').read_text())
sheet=Image.open(p/'raw.png');sx=sheet.width/job['sheet_size'][0];sy=sheet.height/job['sheet_size'][1]
reports={};base=None
for cell in job['cells']:
 k=cell['asset'];b=cell['cell'];box=[round(v*(sx if i%2==0 else sy)) for i,v in enumerate(b)]
 # Raw lower row repeats the stand 617 pixels below the first, not 627.
 if b[1]:box[1]-=10;box[3]-=10
 crop=sheet.crop(tuple(box))
 clean,stats=clean_soft(crop,[0,255,255]);cell['native_bounds']=sources[k]['native_bounds']
 clean.save(p/(k+'.master.png'));out,reg=register_cell(clean,job,cell,sheet.size,adjust=(0.83,0.,-5.))
 a=np.array(out)
 Image.fromarray(a).save(p/(k+'.png'))
 reports[k]={'cleanup':stats,'registration':reg}
(p/'extraction_correction.json').write_text(json.dumps({'reason':'Reviewed bone, dark stand and orange flames have no cyan material; extract actual cyan backdrop to preserve base and candle flames. No support replacement applied.','frames':reports},indent=2))
check_existing(job,sources,p)
