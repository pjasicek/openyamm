"""Restore separate stepping stones with AI silhouettes and native contact shade."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import cv2
from scipy.ndimage import gaussian_filter, label, distance_transform_edt, binary_fill_holes
from PIL import ImageDraw
from common import *

F=Path(__file__).resolve().parent


def main():
    receipts=json.loads((F/'generation_receipts.json').read_text())
    assert receipts['count']==24
    for record in receipts['outputs']:
        for key in ('raw','prompt'):
            assert sha(ROOT/record[key])==record[key+'_sha256'],record[key]
        for reference in record['references']:
            assert sha(ROOT/reference['path'])==reference['sha256'],reference['path']
    native_bg=read(P/'references/plntyl.png',512)
    master=read(M/'materials/plains.png')
    reports=[]
    for raw in sorted((F/'raw').glob('*.png')):
        name=raw.stem;mask_path=F/'raw_masks'/(name+'.png')
        if not mask_path.exists():continue
        native=read(P/'references'/(name+'.png'),512)
        generated=read(raw,512)
        mask=read(mask_path,512).mean(2)>127
        labels,count=label(mask)
        # Fill only each stone's interior; never fill the gaps between stones.
        mask=np.logical_or.reduce([binary_fill_holes(labels==i) for i in range(1,count+1)])
        assert label(mask)[1]==count
        alpha=np.clip(gaussian_filter(mask.astype(float),.65),0,1)
        inside=alpha>.9
        a,b=native[inside],generated[inside]
        coloured=(generated-b.mean(0))*np.clip(a.std(0)/np.maximum(b.std(0),1),.65,1.35)+a.mean(0)
        # Only broad forms drive registration; native material noise is not geometry.
        grey=lambda a:seams.byte(gaussian_filter(a.mean(2),4))
        flow=cv2.calcOpticalFlowFarneback(grey(native),grey(coloured),None,.5,4,45,5,7,1.5,0)
        flow=gaussian_filter(flow,(5,5,0))
        yy,xx=np.mgrid[:512,:512]
        aligned=cv2.remap(coloured.astype('float32'),(xx+flow[:,:,0]).astype('float32'),
                         (yy+flow[:,:,1]).astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        distance=distance_transform_edt(~mask)
        contact=np.clip((12-distance)/10,0,1)
        ratio=np.clip(native.mean(2)/np.maximum(native_bg.mean(2),1),.4,1)
        shade=1+(gaussian_filter(ratio,1.5)-1)*contact
        # Exposed-earth borders meet the unshaded periodic master. A faint
        # antialiasing tail is not a physical stone crossing the boundary.
        for side in 'NSEW':
            edge = alpha[0] if side=='N' else alpha[-1] if side=='S' else alpha[:,0] if side=='W' else alpha[:,-1]
            if edge.max()>.5:
                continue
            for depth in range(12):
                strength=np.clip((depth-3)/8,0,1)
                if side=='N':shade[depth]=1+(shade[depth]-1)*strength
                elif side=='S':shade[-1-depth]=1+(shade[-1-depth]-1)*strength
                elif side=='W':shade[:,depth]=1+(shade[:,depth]-1)*strength
                else:shade[:,-1-depth]=1+(shade[:,-1-depth]-1)*strength
        pixels=aligned*alpha[:,:,None]+master*shade[:,:,None]*(1-alpha[:,:,None])
        # Extend stone paint; wrap the periodic master under exposed earth only.
        padded=seams.pad(pixels,'edge')
        padded+=(seams.pad(master,'wrap')-seams.pad(master,'edge'))*(1-seams.pad(alpha,'edge')[:,:,None])
        save(F/'authoring'/(name+'.png'),pixels)
        save(F/'runtime'/(name+'.png'),seams.reduce(padded))
        save(F/'masks'/(name+'.png'),alpha*255)
        save(F/'shading'/(name+'.png'),shade*255)
        (F/'fields').mkdir(exist_ok=True)
        np.savez_compressed(F/'fields'/(name+'.npz'),alpha=alpha,shade=shade,rgb=aligned)
        reports.append(dict(name=name,components=count,raw_sha256=sha(raw),mask_raw_sha256=sha(mask_path),
                            runtime_sha256=sha(F/'runtime'/(name+'.png')),max_flow=float(np.linalg.norm(flow,axis=2).max())))
    sheet=Image.new('RGB',(1024,280*len(reports)),'#202933');draw=ImageDraw.Draw(sheet)
    for row,r in enumerate(reports):
        n=r['name']
        for col,path in enumerate((P/'references'/(n+'.png'),F/'raw'/(n+'.png'),F/'runtime'/(n+'.png'),F/'masks'/(n+'.png'))):
            sheet.paste(Image.open(path).convert('RGB').resize((256,256)),(col*256,row*280+24))
            draw.text((col*256+4,row*280+5),n+' '+['native','raw AI','composite','stone mask'][col],fill='white')
    sheet.save(F/'comparison.png')
    for group in range(4):
        sheet.crop((0,group*840,1024,(group+1)*840)).save(F/('comparison_%d.png'%(group+1)))
    (F/'build.json').write_text(json.dumps(dict(status='family_candidates_not_runtime_installed',tiles=reports,
        receipts_sha256=sha(F/'generation_receipts.json'),
        master_sha256=sha(M/'materials/plains.png'),script_sha256=sha(Path(__file__))),indent=2)+'\n')
    print([(r['name'],r['components'],round(r['max_flow'],2)) for r in reports])


if __name__=='__main__':main()
