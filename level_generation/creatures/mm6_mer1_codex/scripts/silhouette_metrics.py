import sys,json,numpy as np
from pathlib import Path
from PIL import Image
ref,cur=map(Path,sys.argv[1:]);rows={}
for f in sorted(cur.glob('*.png')):
 a=np.asarray(Image.open(ref/f.name))[:,:,3]>127;b=np.asarray(Image.open(f))[:,:,3]>127;assert a.any()
 rows[f.name]={'iou':float((a&b).sum()/(a|b).sum()),'reference_pixels':int(a.sum()),'candidate_pixels':int(b.sum())}
assert len(rows)>=8
print(json.dumps({'views':rows,'min_iou':min(r['iou']for r in rows.values()),'min_ssim':None,'measurement':'geometry exploration; rebaked tier materials measured on the selected candidate'}))
