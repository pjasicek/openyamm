"""Compose imagegen coverage masks with accepted materials and explicit shared boundary constraints."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

P=Path(__file__).resolve().parent
STUDY=P.parent/'mm6_new_sorpigal_master_study'
BASES={'6dirttyl':'dirt','6grastyl':'grass','6voltyl':'volcano'}


def linear(a):
    a=a/255.0
    return np.where(a<=0.04045,a/12.92,((a+0.055)/1.055)**2.4)


def srgb(a):
    return np.rint(np.clip(np.where(a<=0.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-0.055),0,1)*255).astype('uint8')


def edge(a,s):
    return {'N':a[0],'S':a[-1],'W':a[:,0],'E':a[:,-1]}[s]


def sdf(a):
    if a.all():return np.full(a.shape,32.)
    if not a.any():return np.full(a.shape,-32.)
    return np.clip(distance_transform_edt(a)-distance_transform_edt(~a),-32,32)


def main():
    inventory=json.loads((P/'mask_inventory.json').read_text())['masks']
    byname={r['tile']:r for r in inventory}
    masks={}
    for r in inventory:
        name=r['tile'];source=P/'masks/v1'/(name+'.png')
        if name=='6drsrew':source=P/'raw/6drsrew_v2.png'
        with Image.open(source) as im:
            masks[name]=np.asarray(im.convert('L').resize((512,512),Image.Resampling.LANCZOS))>=128
        if name=='6grdrtxne':
            with Image.open(P/'raw/6grdrtxne_v2.png') as im:
                repair=np.asarray(im.convert('L').resize((512,512),Image.Resampling.LANCZOS))>=128
            masks[name]=repair
    constraints=json.loads((P/'adjacency_constraints.json').read_text())
    # Match all sides with the same topology/axis, including newly valid map-correction joins.
    # Crossings are measured from the AI masks, never from original RGB colour thresholds.
    profiles={};measurements={}
    for name,r in byname.items():
        for side,topology in r['edge_topology'].items():
            key=('horizontal' if side in 'NS' else 'vertical')+':'+topology
            measurements.setdefault(key,[]).append(edge(masks[name],side))
    for key,edges in measurements.items():
        topology=key.split(':',1)[1]
        if topology=='dirt/dirt':a=np.zeros(512,dtype=bool)
        elif topology in ('grass/grass','volcano/volcano'):a=np.ones(512,dtype=bool)
        else:
            a=np.median(np.stack(edges).astype(float),axis=0)>=.5
            if topology!='road_opening':
                crossings=np.where(np.diff(a.astype(int))!=0)[0]+1
                crossing=int(np.median(crossings[(crossings>128)&(crossings<384)]))
                a=np.arange(512)<crossing
                if topology.startswith('dirt/'):a=~a
        profiles[key]=a
    # Keep the reviewed v2 edge contract fixed during this interior mask repair.
    for key,record in json.loads((P/'reports/shared_profiles_v2.json').read_text()).items():
        profiles[key]=np.zeros(512,dtype=bool)
        for start,end in record['white_intervals']:profiles[key][start:end]=True
    export=P/'composites/v4';fixed=P/'masks/connected_v4';runtime=P/'runtime_x2/worlds/mm6/terrain_x2'
    for d in (export,fixed,runtime):d.mkdir(parents=True,exist_ok=True)
    profile_report={}
    for key,a in profiles.items():
        starts=np.where(np.diff(np.r_[False,a,False].astype(int))==1)[0]
        ends=np.where(np.diff(np.r_[False,a,False].astype(int))==-1)[0]
        profile_report[key]={'white_intervals':list(map(list,zip(starts.tolist(),ends.tolist()))),
                             'crossings':(np.where(np.diff(a.astype(int))!=0)[0]+1).tolist()}
    (P/'reports/shared_profiles_v4.json').write_text(json.dumps(profile_report,indent=2)+'\n')
    decisions=json.loads((STUDY/'material_decisions.json').read_text())
    materials={}
    for material in ['dirt','grass','volcano','cobbles']:
        source=STUDY/decisions[material]['master_png']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==decisions[material]['master_sha256']
        derivative=P/'material_seams/connected_v2'/(material+'.png')
        materials[material]=linear(np.asarray(Image.open(derivative).convert('RGB'),dtype=float))
    reports=[]
    for r in inventory:
        name=r['tile'];original=masks[name];field=sdf(original)
        # 8px locked strip, smooth signed-distance approach through 24px more; no wide gray crossfade.
        for side,topology in r['edge_topology'].items():
            key=('horizontal' if side in 'NS' else 'vertical')+':'+topology
            target=sdf(profiles[key])
            for depth in range(32):
                t=np.clip((depth-8)/24,0,1);weight=1-t*t*(3-2*t)
                if side=='N':field[depth,:]=field[depth,:]*(1-weight)+target*weight
                elif side=='S':field[-1-depth,:]=field[-1-depth,:]*(1-weight)+target*weight
                elif side=='W':field[:,depth]=field[:,depth]*(1-weight)+target*weight
                else:field[:,-1-depth]=field[:,-1-depth]*(1-weight)+target*weight
        coverage=np.clip(field/2+.5,0,1)
        mask=np.rint(coverage*255).astype('uint8');Image.fromarray(mask).save(fixed/(name+'.png'))
        coverage=mask.astype(float)[:,:,None]/255
        composite=srgb(materials['dirt']*(1-coverage)+materials[r['white']]*coverage)
        image=Image.fromarray(composite);image.save(export/(name+'.png'))
        image.resize((256,256),Image.Resampling.LANCZOS).save(runtime/(name+'.png'))
        reports.append({'tile':name,'changed_mask_fraction':float(np.mean((mask>=128)!=original)),
                        'interior_unchanged':bool(np.array_equal((mask>=128)[32:-32,32:-32],original[32:-32,32:-32]))})
    for name,material in BASES.items():
        image=Image.fromarray(srgb(materials[material]));image.save(export/(name+'.png'))
        image.resize((256,256),Image.Resampling.LANCZOS).save(runtime/(name+'.png'))
    (P/'reports/composition_v4.json').write_text(json.dumps({'masks':reports,'blend':'linear-light',
        'mask_normalization':'AI coverage threshold at128, shared edge SDF constraints and narrow antialias',
        'locked_strip':8,'repair_zone':24,'masters':'seam derivatives; accepted central448x448 interiors unchanged',
        'runtime_size':256,'authoring_size':512},indent=2)+'\n')
    for family in ['grass_dirt','rock_dirt','roads']:
        names=[r['tile'] for r in inventory if r['family']==family]
        sheet=Image.new('RGB',(4*384,((len(names)+3)//4)*410),'#202933');draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(names):
            x=i%4*384;y=i//4*410
            draw.text((x+4,y+3),name,fill='white')
            with Image.open(runtime/(name+'.png')) as im:sheet.paste(im.resize((384,384)),(x,y+24))
        sheet.save(P/'reports'/(family+'_composites_v4.png'))
    print('Composed 33 connected masks and 36 native runtime tiles.')


if __name__=='__main__':main()
