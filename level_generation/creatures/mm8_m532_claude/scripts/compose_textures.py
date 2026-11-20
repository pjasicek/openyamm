"""Native A/B/C harness ramps, graded coat/hair, and per-class specular/roughness maps."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures'
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parent/'mm6_gob_claude/scripts'));import compose_textures_v2 as C
C.SIZE=1024;N=1024;D=np.load(P/'work/uv3d.npz');faces=D['faces'];co=D['vertices'];parts=D['component'];head=D['head']
def load(path,mode='RGB'):return np.array(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,name):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(T/name)
def pad(a,cov):
    _,ix=ndimage.distance_transform_edt(~cov,return_indices=True);return a[tuple(ix)]
def raster(which):
    take=head.astype(bool)==which;d={'uv':D['head_uv'if which else'uv'][take],'xyz':co[faces[take]],'part':parts[faces[take,0]]}
    return C.rasterise(d,tol=0)
sets={};report={}
for ishead,prefix,job in [(False,'centaur','body_texture_v1'),(True,'centaur_head','head_texture_v1')]:
    part,xyz=raster(ishead);cov=part>=0;src=P/'meshy'/job
    base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');mr=load(src/'texture_urls_0_metallic.png','L');rough=load(src/'texture_urls_0_roughness.png','L')
    h,s,v=C.hsv(base);x,y,z=xyz.transpose(2,0,1)
    green=cov&(h>72)&(h<175)&(s>.25)&(v>.13)
    tail=cov&(part!=0)&(y>.83);hair=cov&(part!=0)&(z>1.9)
    skin=cov&(part==0)&(z>1.42)&(h<48)&(s>.15)&(v>.32)
    metal=cov&((mr>.55)|((s<.20)&(v>.28)&(z>.17)))&~skin&~hair&~tail
    coat=cov&(z<1.46)&~tail&~metal
    hoof=cov&(z<.14)
    g=base.copy();g[skin]*=.92;g[coat]*=.80;g[tail]*=.48;g[hair]*=.63
    if ishead:
        # Hair includes beard tones on the connected face, while preserving skin and eye whites.
        beard=cov&(part==0)&(v<.37)&(z>2.20);g[beard]*=.75
    cls=np.zeros((N,N),np.uint8);spec=np.full((N,N),.22);rgh=np.full((N,N),.82)
    for mask,c,sp,rg in [(skin,1,.35,.72),(coat,2,.16,.86),(tail|hair,11,.12,.9),(green,8,.22,.8),(metal,10,.85,.4),(hoof,3,.3,.65)]:
        cls[mask]=c;spec[mask]=sp;rgh[mask]=np.clip(rg+(rough[mask]-np.median(rough[mask]))*.15,.2,1) if mask.any() else rg
    sets[prefix]={'base':g,'cov':cov,'normal':normal,'mr':np.stack([spec,rgh,np.where(metal,.65,0)],-1),'mask':green,'cls':cls,'pos':xyz,'skin':skin}
    report[prefix]={'covered':int(cov.sum()),'harness_texels':int(green.sum()),'skin_texels':int(skin.sum())}
# Measure both UV layers at actual shared neck edges, using only warm skin samples.
edges={}
for i,f in enumerate(faces):
    for a,b in zip(f,np.roll(f,-1)):edges.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
samples=[[],[]]
for edge,fs in edges.items():
    if len(fs)!=2 or head[fs[0]]==head[fs[1]]:continue
    pair=[]
    for fi in fs:
        which=bool(head[fi]);uv=D['head_uv'if which else'uv'][fi];idx=[k for k,v in enumerate(faces[fi])if v in edge];p=.65*uv[idx].mean(0)+.35*uv.mean(0)
        xx,yy=np.clip((p[0]*N,(1-p[1])*N),0,N-1).astype(int);rgb=sets['centaur_head'if which else'centaur']['base'][yy,xx]
        pair.append((int(which),rgb))
    if all(rgb[0]>rgb[1]*1.08 and rgb.mean()>.25 for _,rgb in pair):
        for which,rgb in pair:samples[which].append(rgb)
assert len(samples[0])>5,'No measured skin seam'
gain=np.median(samples[0],0)/np.maximum(np.median(samples[1],0),.001);gain=np.clip(gain,.75,1.3)
H=sets['centaur_head'];H['base'][H['skin']]*=gain
report['neck_seam']={'samples':len(samples[0]),'rgb_gain':gain.tolist()}
# Native indexed pixels, same differing palette entries, rank matched to harness luminance.
palroot=P.parents[2]/'assets_dev/worlds/mm8/textures'
# Project is three levels below the repository.
palroot=Path(__file__).resolve().parents[4]/'assets_dev/worlds/mm8/textures'
pals={k:np.frombuffer((palroot/f'pal{pid}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,pid in [('centaur_a',533),('centaur_b',534),('centaur_c',535)]}
differ=(np.abs(pals['centaur_a']-pals['centaur_b']).sum(1)>.02)|(np.abs(pals['centaur_a']-pals['centaur_c']).sum(1)>.02)
indices=[]
source={r['frame']:r['source']for r in json.loads((P/'native/inventory.json').read_text())}
for f in ('sa0','sa1','sa2','sa3','sa4','aa0','ac0','ae2','wa0','wc2'):
    idx=np.array(Image.open(Path(__file__).resolve().parents[4]/source['m532'+f]));indices.extend(idx[differ[idx]].tolist())
indices=np.array(indices);assert len(indices)>100
B=sets['centaur'];lum=R.luminance(B['base'][B['mask']]);lo,hi=np.percentile(lum,[2,98]);ordered=np.sort(lum);ramps={}
for k,pal in pals.items():
    col=pal[indices];l=R.luminance(col);col=col[l>.01];col=col[np.argsort(R.luminance(col))];colors=[]
    for i in range(16):
        q=np.searchsorted(ordered,lo+(hi-lo)*i/15)/len(ordered);c=col[min(len(col)-1,int(q*(len(col)-1)))];colors.append(R.srgb_to_linear(np.clip(c*1.30,0,1)).tolist())
    ramps[k]=[{'range':[float(lo),float(hi)],'colors':colors}]
# The packed body islands leave no safe 64-pixel square; give props a narrow atlas strip.
prop_size=128;x0=1024;y0=448;rect=(x0,y0,prop_size,prop_size)
props=np.array(Image.open(T/'centaur_props.png').convert('RGB').resize((prop_size,prop_size),Image.Resampling.LANCZOS),float)/255
strip=np.broadcast_to(np.arange(prop_size)[None,:]//(prop_size//8),(prop_size,prop_size))
pmr=np.stack([np.where(np.isin(strip,[1,6]),.8,.2),np.where(np.isin(strip,[1,6]),.4,.78),np.where(np.isin(strip,[1,6]),.6,0)],-1)
report['props_rect_pixels']=rect;report['body_texture_dimensions']=[1152,1024]
for prefix,S in sets.items():
    cov=S['cov'];base=pad(S['base'],cov);normal=pad(S['normal'],cov);mr=pad(S['mr'],cov)
    if prefix=='centaur':
        base=np.pad(base,((0,0),(0,128),(0,0)),mode='edge');normal=np.pad(normal,((0,0),(0,128),(0,0)),mode='edge');mr=np.pad(mr,((0,0),(0,128),(0,0)),mode='edge')
        base[y0:y0+prop_size,x0:x0+prop_size]=props;normal[y0:y0+prop_size,x0:x0+prop_size]=(.5,.5,1);mr[y0:y0+prop_size,x0:x0+prop_size]=pmr
    save(base,prefix+'_basecolor_1k.png');save(normal,prefix+'_normal_1k.png');save(mr,prefix+'_metal_rough_1k.png')
    classes=S['cls']
    if prefix=='centaur':
        classes=np.pad(classes,((0,0),(0,128)));classes[y0:y0+prop_size,x0:x0+prop_size]=np.where(np.isin(strip,[1,6]),10,6)
    Image.fromarray(classes).save(T/(prefix+'_material_classes.png'))
mask=np.pad(ndimage.gaussian_filter(pad(B['mask'].astype(float),B['cov']),.6),((0,0),(0,128))); mask[y0-4:y0+prop_size+4,x0-4:x0+prop_size+4]=0
R.write_mask([mask],T/'centaur_region_mask.png',size=(1152,1024))
R.write_mask([ndimage.gaussian_filter(pad(H['mask'].astype(float),H['cov']),.6)],T/'centaur_head_region_mask.png')
(T/'centaur_ramps.json').write_text(json.dumps({'variants':list(pals),'materials':[{'base':'Centaur','prefix':'Centaur','mask':'centaur_region_mask.png','regions':['harness'],'ramps':ramps},{'base':'CentaurHead','prefix':'CentaurHead','mask':'centaur_head_region_mask.png','regions':['harness'],'ramps':ramps}]},indent=2)+'\n')
(T/'texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

cfg=json.loads((T/'centaur_ramps.json').read_text())
import copy
for joint in ('Bow','Quiver'):
    m=copy.deepcopy(cfg['materials'][0]);m['base']=m['prefix']='Centaur'+joint;cfg['materials'].append(m)
(T/'centaur_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
