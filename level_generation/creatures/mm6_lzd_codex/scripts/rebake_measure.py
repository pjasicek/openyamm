import json,sys,numpy as np
from pathlib import Path
from PIL import Image
from round3_reduction_metrics import compare
P=Path(__file__).resolve().parents[1]
def measure(tag,level,views=8,parts=('body','bow'),reference='reference_pbr'):
 result={}
 for part in parts:
  rows=[];intersection=union=0
  for i in range(views):
   a=P/f'review/rebake/{reference}_{part}_l{level}_{i}.png';b=P/f'review/rebake/{tag}_{part}_l{level}_{i}.png';rows.append(compare(a,b));ma=np.asarray(Image.open(a).convert('RGBA'))[...,3]>=128;mb=np.asarray(Image.open(b).convert('RGBA'))[...,3]>=128;intersection+=int((ma&mb).sum());union+=int((ma|mb).sum())
  r={'views':rows,'pooled_iou':intersection/union,'min_iou':min(v['iou']for v in rows),'min_ssim':min(v['ssim']for v in rows)};r['passed']=r['min_iou']>=.99 and r['min_ssim']>=.95 if level==0 else r['pooled_iou']>=.97;result[part]=r
 return result
if __name__=='__main__':print(json.dumps(measure(sys.argv[1],int(sys.argv[2]),int(sys.argv[3])if len(sys.argv)>3 else 8,[sys.argv[4]]if len(sys.argv)>4 else ['body','bow'],sys.argv[5]if len(sys.argv)>5 else 'reference_pbr')))
