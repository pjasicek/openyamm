"""Recover native MM6 coverage/contact shade, compose connected 2x terrain variants.

Original RGB is used only to estimate scalar fields. Every material sample comes
from the accepted restored masters, at one fixed phase. No original grain overlay.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, shutil, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_fill_holes
P=Path(__file__).resolve().parent
R=P.parent; T=R.parent; ROOT=T.parents[1]
spec=importlib.util.spec_from_file_location('terrain_seam_helpers',T/'seam_repair/build.py')
seams=importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)
D=T/'mm6_new_sorpigal_dirt_fidelity/transitions'
OLD=D/'shorelines/runtime_x2/worlds/mm6/terrain_x2'
MASTER=R/'masters/v3'
OUT=P/'runtime_x2/worlds/mm6/terrain_x2'

def read(p): return np.asarray(Image.open(p).convert('RGB'),float)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def edge(a,side):
    if side=='N':return a[0]
    if side=='S':return a[-1]
    if side=='W':return a[:,0]
    return a[:,-1]
def line(a,side,depth):
    if side=='N':return a[depth]
    if side=='S':return a[-1-depth]
    if side=='W':return a[:,depth]
    return a[:,-1-depth]
def up(a): return np.asarray(Image.fromarray(a.astype('float32'),'F').resize((512,512),Image.Resampling.BICUBIC),float)
def recover(original,dirt,material):
    a,d,m=original/255,dirt/255,material/255
    dd=(d*d).sum(2);mm=(m*m).sum(2);dm=(d*m).sum(2);da=(d*a).sum(2);ma=(m*a).sum(2)
    det=np.maximum(dd*mm-dm*dm,1e-8)
    wd=(da*mm-ma*dm)/det;wm=(ma*dd-da*dm)/det
    neg=wd<0;wd[neg]=0;wm[neg]=ma[neg]/np.maximum(mm[neg],1e-8)
    neg=wm<0;wm[neg]=0;wd[neg]=da[neg]/np.maximum(dd[neg],1e-8)
    shade=wd+wm;alpha=np.clip(wm/np.maximum(shade,1e-8),0,1)
    same_d=np.max(abs(original-dirt),axis=2)<=3
    same_m=np.max(abs(original-material),axis=2)<=3
    alpha[same_d]=0;alpha[same_m]=1
    # Native contact shade is a separate scalar, not mistaken for dirt coverage.
    blend=d*(1-alpha[:,:,None])+m*alpha[:,:,None]
    shade=np.sum(a*blend,2)/np.maximum(np.sum(blend*blend,2),1e-8)
    shade[same_d|same_m]=1
    shade=np.clip(shade,.45,1.15)
    # Suppress numerical excursions where nearly brown-on-brown bases are ambiguous.
    shade=gaussian_filter(shade,.55)
    return np.clip(up(alpha),0,1),np.clip(up(shade),.45,1.15),float(np.mean(abs(a-blend*shade[:,:,None]))*255)

def topology(a,side,road=False):
    e=edge(a,side)
    if road:return 'opening' if np.mean(e[180:330])>.5 else '0'
    ends=(int(np.mean(e[12:72])>.5),int(np.mean(e[-72:-12])>.5))
    return str(ends[0])+str(ends[1])

def connect(a,targets,width=40):
    for side,target in targets.items():
        for depth in range(width):
            t=np.clip((depth-8)/(width-8),0,1);w=1-t*t*(3-2*t)
            v=line(a,side,depth);v[:]=v*(1-w)+target*w
    return a

def main():
    inv=json.loads((R/'inventory.json').read_text());groups={g['id']:g for g in inv['groups']}
    for name in ('masks','shading','authoring','sheets','contexts','fields','reports'): (P/name).mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    for source in OLD.glob('*.png'):shutil.copy2(source,OUT/source.name)
    for source in (MASTER/'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):shutil.copy2(source,OUT/source.name)
    native_d=read(ROOT/'assets_dev/worlds/mm6/textures/6dirttyl.bmp')
    materials={g:read(MASTER/'materials'/(g+'.png')) for g in groups if g!='roads'}
    materials['roads']=read(D/'seam_repair/materials/cobbles.png')
    dirt=read(D/'seam_repair/materials/dirt.png')
    native={g:read(R/'references'/(v['base']+'.png')) for g,v in groups.items() if g!='roads'}
    roads=np.stack([read(p) for p in (ROOT/'assets_dev/worlds/mm6/textures').glob('6drsr*.bmp')])
    chroma=(roads[:,:,:,0]-roads[:,:,:,2])/np.maximum(roads.mean(3),1)
    pick=chroma.argmin(0);yy,xx=np.mgrid[:128,:128];native['roads']=roads[pick,yy,xx]
    records=[r for r in inv['tiles'] if r['kind']!='base'];fields={};measurements=collections.defaultdict(list)
    for r in records:
        assert sha(ROOT/r['source'])==r['source_sha256']
        name=r['name'];g=r['family'];a,s,error=recover(read(R/r['reference']),native_d,native[g])
        if g=='roads':
            original=read(R/r['reference'])
            chroma=(original[:,:,0]-original[:,:,2])/np.maximum(original.mean(2),1)
            # Grey stones and brown earth have distinct chroma even in shadow.
            # Road source dirt/stones do not share the base tile's sampling phase.
            stones=binary_fill_holes(chroma<.40)
            a=np.clip(up(stones.astype(float)),0,1)
            boundary=distance_transform_edt(a>.5)+distance_transform_edt(a<=.5)
            s=1-(1-np.minimum(s,1))*np.clip((16-boundary)/12,0,1)
        else:
            bulk=gaussian_filter(a,8)>.5
            inside=distance_transform_edt(bulk);outside=distance_transform_edt(~bulk)
            a[inside>48]=1;a[outside>48]=0
            s[(inside>48)|(outside>48)]=1
        fields[name]=dict(alpha=a,shade=s,error=error,topology={side:topology(a,side,g=='roads') for side in 'NSEW'})
        if name=='crkdrtnw':
            # Brown cracked earth confuses the colour fit at the southwest corner.
            # The native NW outer corner has dirt at SW, cracked material at SE.
            fields[name]['topology']['S']='01'
        for side,kind in fields[name]['topology'].items():
            key=(g,'h' if side in 'NS' else 'v',kind)
            measurements[key].append((edge(a,side),edge(s,side)))
    profiles={}
    for (g,axis,kind),values in measurements.items():
        if kind in ('0','00','11'):
            a=np.full(512,1. if kind=='11' else 0.);s=np.ones(512)
        elif g=='roads':
            source='6drsrns' if axis=='h' else '6drsrew';side='N' if axis=='h' else 'W'
            a=edge(np.asarray(Image.open(D/'masks/connected_v4'/(source+'.png')),float)/255,side).copy()
            s=np.ones(512)
        else:
            a=np.median(np.stack([v[0] for v in values]),axis=0)
            s=np.median(np.stack([v[1] for v in values]),axis=0)
            # Corners are a pure material; all four neighbours share that contract.
            a[:32]=int(kind[0]);a[-32:]=int(kind[-1]);s[:32]=s[-32:]=1
        profiles[(g,axis,kind)]=(a,s)
    reports=[]
    for r in records:
        name=r['name'];g=r['family'];f=fields[name]
        at={};st={}
        for side,kind in f['topology'].items():
            a,s=profiles[(g,'h' if side in 'NS' else 'v',kind)];at[side]=a;st[side]=s
        a=connect(f['alpha'].copy(),at);s=connect(f['shade'].copy(),st)
        # Contact shading remains local to the original material boundary.
        Image.fromarray(seams.byte(a*255)).save(P/'masks'/(name+'.png'))
        Image.fromarray(seams.byte(s*200)).save(P/'shading'/(name+'.png'))
        np.savez_compressed(P/'fields'/(name+'.npz'),coverage=a.astype('float32'),shade=s.astype('float32'))
        base=seams.linear(seams.pad(dirt,'wrap'))*(1-seams.pad(a,'edge')[:,:,None])+seams.linear(seams.pad(materials[g],'wrap'))*seams.pad(a,'edge')[:,:,None]
        rgb=seams.srgb(base).astype(float)*seams.pad(s,'edge')[:,:,None]
        if g=='roads':
            delta=seams.linear(np.clip(rgb,0,255))-base
            inner=delta[8:-8,8:-8].copy();targets={}
            for side,kind in f['topology'].items():
                if kind=='0':targets[side]=np.zeros((512,3))
                else:
                    source='6drsrns' if side in 'NS' else '6drsrew'
                    targets[side]=edge(np.load(D/'edge_treatment/layers/v1'/(source+'.npz'))['linear_rgb_delta'],side).copy()
            inner=connect(inner,targets);rgb=seams.srgb(base+seams.pad(inner,'edge'))
        Image.fromarray(seams.byte(rgb[8:-8,8:-8])).save(P/'authoring'/(name+'.png'))
        Image.fromarray(seams.reduce(rgb)).save(OUT/(name+'.png'))
        reports.append(dict(tile=name,family=g,source_sha256=r['source_sha256'],reconstruction_mean_absolute_error= f['error'],edge_topology=f['topology'],shade_min=float(s.min()),shade_below_95_fraction=float(np.mean(s<.95)),runtime_sha256=sha(OUT/(name+'.png'))))
    files={p.name:sha(p) for p in OUT.glob('*.png')}
    assert len(files)==134,len(files)
    assert all(sha(p)==files[p.name] for p in OLD.glob('*.png'))
    expected={n for m in inv['maps'] for n in m['used_tiles']}
    assert expected <= {Path(n).stem for n in files}
    for g in groups:
        members=[r for r in records if r['family']==g]
        sheet=Image.new('RGB',(1024,280*len(members)),'#202933');draw=ImageDraw.Draw(sheet)
        for row,r in enumerate(members):
            name=r['name']
            ims=[Image.open(R/r['reference']).resize((256,256),Image.Resampling.NEAREST),Image.open(OUT/(name+'.png')),Image.open(P/'masks'/(name+'.png')).resize((256,256)),Image.open(P/'shading'/(name+'.png')).resize((256,256))]
            for col,im in enumerate(ims):sheet.paste(im,(col*256,row*280+24));draw.text((col*256+4,row*280+5),name+' '+['original','x2','coverage','shade: neutral=200'][col],fill='white')
        sheet.save(P/'sheets'/(g+'.png'))
    report=dict(method='Native per-pixel nonnegative two-material decomposition; scalar alpha and shade transferred to restored masters. Shared axis/topology edge profiles. Fixed material phase, wrapped material gutters and edge-extended scalar fields. Road openings reuse accepted masks and linear edge deltas.',authoring_size=512,runtime_size=256,tiles=reports,preserved_existing_files=63,total_files=len(files),covered_static_tiles=len(expected),covered_maps=len(inv['maps']))
    (P/'reports/build.json').write_text(json.dumps(report,indent=2)+'\n')
    (P/'runtime_x2/manifest.json').write_text(json.dumps(dict(iteration='mm6_complete_terrain_v1',size=[256,256],files={'worlds/mm6/terrain_x2/'+n:h for n,h in sorted(files.items())}),indent=2)+'\n')
    (P/'reports/edge_profiles.json').write_text(json.dumps({':'.join(k):dict(coverage=a.tolist(),shade=s.tolist()) for k,(a,s) in profiles.items()},indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tiles'},indent=2))
if __name__=='__main__':main()
