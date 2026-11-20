"""Select raw generated views that meet the unchanged registration gate; never rescale artwork."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1]
VIEWS=['front','back','left','right','top']
def extent(image):
    y,x=np.nonzero(np.array(image.convert('RGBA'))[:,:,3]>127)
    return x.max()-x.min(),y.max()-y.min()
for icon in sys.argv[1:]:
    folder=P/f'codex_tex/equipment_{icon}';report={};fail=[]
    for i,view in enumerate(VIEWS):
        reference=extent(Image.open(folder/f'guide_{view}.png'))
        for kind,row in [('paint',0),('mask',2)]:
            candidates=[]
            for raw in sorted(folder.glob('paint_mask_raw_v*.png')):
                sheet=Image.open(raw);cell=sheet.width//3
                crop=sheet.crop((i%3*cell,(i//3+row)*cell,(i%3+1)*cell,(i//3+row+1)*cell))
                measured=extent(crop.resize((1024,1024),Image.Resampling.NEAREST))
                ratios=[measured[k]/reference[k] for k in range(2)]
                candidates.append((max(abs(x-1) for x in ratios),raw,crop,ratios))
            score,raw,crop,ratios=min(candidates,key=lambda x:x[0])
            crop.save(folder/f'{kind}_{view}.png')
            report[f'{kind}_{view}']={'raw':raw.name,'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'tile':i+row*3,'ratios':ratios,'strict_pass':bool(score<=.05+2/1024)}
            if score>.05+2/1024:fail.append(f'{kind}_{view}: {ratios}')
    frame=json.loads((folder/'views.json').read_text());frame['paint_layout']='individual';frame['mask_layout']='individual'
    (folder/'views.json').write_text(json.dumps(frame,indent=2)+'\n')
    (folder/'selected_views.json').write_text(json.dumps(report,indent=2)+'\n')
    print(icon,'all raw views registered' if not fail else '; '.join(fail))
