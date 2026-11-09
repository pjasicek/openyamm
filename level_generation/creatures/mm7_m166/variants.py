"""Enhanced tentacle-tip masks and fixed native ACT palette transforms."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent/'mm7_m514'))
from process import apply_variant


def run():
    sources = json.loads((HERE/'sources.json').read_text())
    palettes = {p: np.frombuffer((REPO/f'assets_dev/worlds/mm7/textures/pal{p}.act').read_bytes()[:768],
                                np.uint8).reshape(256,3).astype(float) for p in [167,168,169]}
    base = palettes[167]
    ids = np.arange(150,220)
    ids = ids[(base[ids,1]>base[ids,0]*1.3)&(base[ids,1]>base[ids,2]*1.3)]
    variants = []
    for p in palettes:
        matrix = np.linalg.lstsq(base[ids], palettes[p][ids], rcond=None)[0]
        variants.append(dict(id=f'mm7:palette{p}', palette_id=p, default=p==167, exact_bypass=p==167,
                             descriptors=[211+p-167], rgb_matrix=matrix.tolist()))
    data = dict(variants=variants, regions=[dict(id='tentacle_tips', channel='R',
        protected='Brown head, green eyes, gray shafts, ivory teeth and gold strands.')],
        recolor=dict(operation='masked_rgb_matrix', color_space='encoded sRGB 0..255',
        rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; exact base bypass',
        native_indices=ids.tolist(), mask_format='R8 linear',
        calibration='Fixed native green tip ACT least-squares RGB fit; enhanced green components with head/eye protection, profile tip geometry, minimum component support to reject eye-rim highlights, and recorded local inclusion/exclusion polygons including detached eyes.',
        mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels.'))
    (HERE/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    registration = json.loads((HERE/'registration.json').read_text())
    records = {}
    corrections=json.loads((HERE/'tip_corrections.json').read_text())
    exclusions=json.loads((HERE/'tip_exclusions.json').read_text())
    for name in registration:
        im = Image.open(HERE/f'aligned_2x/{name}.png')
        a = np.array(im); rgb = a[:,:,:3].astype(float); r,g,b = rgb.transpose(2,0,1); alpha = a[:,:,3]/255
        green = (g-np.maximum(r,b))/np.maximum(g,1)
        brown = (r>g*1.35)&(g>b*1.15)&(alpha>.8)
        labels,count = ndimage.label(brown)
        sizes = np.bincount(labels.ravel()); sizes[0]=0
        head = np.zeros(g.shape,bool)
        if count:
            yy,xx = np.where(labels==sizes.argmax())
            if len(xx)>5:
                points=np.stack((xx,yy),1); hull=ConvexHull(points)
                region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in points[hull.vertices]],fill=255)
                head=ndimage.binary_dilation(np.array(region)>0,iterations=2)
        hy,hx=np.where(head)
        yy_grid,xx_grid=np.indices(g.shape)
        eye_zone=np.zeros(g.shape,bool)
        brow_tip=np.zeros(g.shape,bool)
        if len(hx):
            head_width=hx.max()-hx.min();head_height=hy.max()-hy.min()
            eye_zone=(xx_grid>hx.min()-head_width*.5)&(xx_grid<hx.max()+head_width*.5)&(yy_grid<hy.max())
            if name[-1]=="2":
                brow_tip=(yy_grid>=hy.min())&(yy_grid<=hy.max())&(xx_grid<hx.min()+head_width*.68)
        labels,count = ndimage.label((green>.3)&(alpha>.5),structure=np.ones((3,3)))
        selected=np.zeros(g.shape,bool); retained=[]
        for label in range(1,count+1):
            yy,xx=np.where(labels==label)
            if len(xx)<25:continue
            eig=np.linalg.eigvalsh(np.cov(np.stack((xx,yy))))
            ratio=eig[1]/max(eig[0],.01)
            elongated_tip = ratio>4.5 and (len(xx)>=100 or max(np.ptp(xx),np.ptp(yy))>=35)
            if (elongated_tip or np.mean(eye_zone[yy,xx])<.2) and np.mean(head[yy,xx]&(~brow_tip[yy,xx]))<.4:
                selected[yy,xx]=True
                retained.append(dict(bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],ratio=float(ratio)))
        distance=ndimage.distance_transform_edt(~selected)
        weight=np.clip((green-.06)/.24,0,1)*(distance<3)*((~head)|brow_tip)*(alpha>0)
        for points in corrections.get(name,[]):
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in points],fill=255)
            weight=np.maximum(weight,np.clip((green-.06)/.24,0,1)*(np.array(region)>0)*(alpha>0))
        for points in exclusions.get(name,[]):
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in points],fill=255)
            weight[np.array(region)>0]=0
        denominator=ndimage.gaussian_filter(alpha,.45)
        weight=ndimage.gaussian_filter(weight*alpha,.45)/np.maximum(denominator,1e-8)
        weight[alpha==0]=0
        Image.fromarray(np.round(weight*255).astype(np.uint8)).save(HERE/f'masks_2x/{name}.png')
        records[name]=retained
    (HERE/'mask_components.json').write_text(json.dumps(records,indent=2)+'\n')
    settings=json.loads((HERE/'processing_settings.json').read_text());settings.update(masks='R8 linear',recolor=data['recolor'])
    (HERE/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    print('Authored',len(registration),'tentacle masks; visual review pending')


if __name__=='__main__':
    run()
