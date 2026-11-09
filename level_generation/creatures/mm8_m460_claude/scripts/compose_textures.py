"""Shared Cleric maps with native hair/staff ramps and per-texel material response."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
p=Path(__file__).resolve().parents[1];root=p.parents[2];T=p/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(root/'tools'));import normal_map_convention as NC
N=1024;normal_reports={}
def load(path,n=N):return np.asarray(Image.open(path).convert('RGB').resize((n,n),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):
    idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);return a[tuple(idx)]
def hsv(a):
    out=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
    return out[...,0]*360,out[...,1],out[...,2]
def normal(path):
    raw=np.asarray(Image.open(path).convert('RGB')).copy();correlation=NC.measure(raw);flip=correlation<=-.15
    if flip:raw[...,1]=255-raw[...,1]
    normal_reports[str(path.relative_to(p))]={'correlation':correlation,'flipped_green':bool(flip)}
    out=np.asarray(Image.fromarray(raw).resize((N,N),Image.Resampling.LANCZOS),float)/255
    v=out*2-1;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-6);return v*.5+.5
palroot=root/'assets_dev/worlds/mm8/textures'
pals={f'm460_{tier}':np.frombuffer((palroot/f'Pal{number}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for tier,number in zip('abc',[461,462,463])}
native=np.asarray(Image.open(root/'assets_dev/engine/sprites/m460Sa0.bmp'));changed=np.max(abs(pals['m460_a']-pals['m460_c']),axis=1)>4/255
hair_indices=np.array(sorted(i for i in np.unique(native[68:116,115:141]) if changed[i] and i!=0))
staff_indices=np.array(sorted(i for i in np.unique(native[67:245,70:92]) if changed[i] and i!=0))
# Exclude the native anti-alias/FX indices that turn cyan highlights purple in the red tier.
a,c=pals['m460_a'],pals['m460_c']
staff_indices=staff_indices[(a[staff_indices,1]>1.4*np.maximum(a[staff_indices,0],a[staff_indices,2])) & (c[staff_indices,0]>1.4*np.maximum(c[staff_indices,1],c[staff_indices,2]))]
assert len(hair_indices)>15 and len(staff_indices)>8
def ramps(base,mask,indices,order_tier):
    lum=R.luminance(base);lo,hi=np.percentile(lum[mask],[1,99]);hi=max(hi,lo+.001)
    order=indices[np.argsort(R.luminance(pals[order_tier][indices]))];out={}
    for tier,pal in pals.items():
        stops=np.stack([np.interp(np.linspace(0,len(order)-1,16),np.arange(len(order)),pal[order,c]) for c in range(3)],axis=1)
        out[tier]=[{'range':[float(lo),float(hi)],'colors':R.srgb_to_linear(stops).round(6).tolist()}]
    return out
maps={};counts={}
for prefix,job,layer in [('m460','body_retexture_v1','UVMap'),('m460_head','head_retexture_v1','HeadUV')]:
    raster=np.load(p/f'work/uvraster_{layer}.npz');piece,pos=raster['piece'],raster['pos'];cov=piece>=0
    base=load(p/f'meshy/{job}/texture_urls_0_base_color.png');nmap=normal(p/f'meshy/{job}/texture_urls_0_normal.png')
    h,s,v=hsv(base);classes=np.zeros((N,N),np.uint8);classes[cov]=8
    classes[np.isin(piece,[0,3,4])]=1
    # The inferred boots are hidden by the native hem except during a step.
    classes[(piece==0)&(pos[...,2]<.18)]=8
    hair=((piece==11)|((piece==1)&(pos[...,2]>1.25)&(abs(pos[...,0])<.135)&(v<.28)&(s<.48)))&cov
    classes[hair]=2;classes[np.isin(piece,[7,8])]=6
    gold=np.isin(piece,[6,9,10,12,13,14,15,16,17])|((piece==1)&~hair&(h>29)&(h<65)&(s>.25)&(v>.48))
    classes[gold]=9
    if prefix.endswith('head'):
        hair=np.isin(piece,[1,11])|((piece==0)&(v<.35)&(s<.5)&((pos[...,2]>1.62)|((abs(pos[...,0])>.065)&(pos[...,2]>1.54)&(pos[...,1]>-.06))));classes[hair]=2
        mouth=(piece==0)&(pos[...,1]<-.08)&(pos[...,2]>1.51)&(pos[...,2]<1.55)&(abs(pos[...,0]+.008)<.031)&(v<.27);classes[mouth]=7
    ao=load(p/f'work/ao_{layer}.png')[...,0];base[cov]*=(.82+.18*np.maximum(ao[cov],.4))[:,None]
    maps[prefix]={'base':base,'normal':nmap,'classes':classes,'covered':cov,'hair':hair,'pos':pos}
# Match the skin boundary between the separate body/head maps, preserving local painted detail.
seams=json.loads((p/'work/seam_samples.json').read_text());skin_seams=[x for x in seams if x['piece']==0]
assert len(skin_seams)>20
tree=cKDTree(np.array([x['pos'] for x in skin_seams]));body=maps['m460'];head=maps['m460_head']
def uv_sample(img,values):
    xy=np.clip(np.floor(np.array(values)*N).astype(int),0,N-1);return img[N-1-xy[:,1],xy[:,0]]
bcol=uv_sample(pad(body['base'],body['covered']),[x['body'] for x in skin_seams])
mask=head['classes']==1;dist,idx=tree.query(head['pos'][mask],k=min(12,len(skin_seams)));w=1/np.maximum(dist,.008)**2
target=(bcol[idx]*w[...,None]).sum(1)/w.sum(1)[:,None];amount=np.clip((.055-dist[:,0])/.04,0,1);amount=amount*amount*(3-2*amount)
head['base'][mask]=head['base'][mask]*(1-amount[:,None])+target*amount[:,None]
# Meet on one skin colour and neutral tangent normal at the head/body boundary.
for data in maps.values():
    mask=(data['classes']==1)&data['covered'];dist,idx=tree.query(data['pos'][mask],k=min(12,len(skin_seams)))
    w=1/np.maximum(dist,.008)**2;target=(bcol[idx]*w[...,None]).sum(1)/w.sum(1)[:,None]
    amount=np.clip((.018-dist[:,0])/.015,0,1);amount=amount*amount*(3-2*amount)
    data['base'][mask]=data['base'][mask]*(1-amount[:,None])+target*amount[:,None]
    amount=np.clip((.025-dist[:,0])/.022,0,1);amount=amount*amount*(3-2*amount)
    n=(data['normal'][mask]*2-1)*(1-amount[:,None])+np.array([0,0,1])*amount[:,None]
    n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-6);data['normal'][mask]=n*.5+.5
response={0:(0,1,0),1:(0,.83,0),2:(.02,.92,0),6:(1,.18,0),7:(.1,.65,0),8:(.04,.86,0),9:(1,.43,0)}
materials=[]
for prefix,data in maps.items():
    base,nmap,classes,cov,hair=[data[k] for k in ['base','normal','classes','covered','hair']]
    mr=np.zeros((N,N,3))
    for key,value in response.items():mr[classes==key]=value
    for suffix,img in [('basecolor',base),('normal',nmap),('metal_rough',mr)]:save(pad(img,cov),T/f'{prefix}_{suffix}_1k.png')
    Image.fromarray(classes).save(T/f'{prefix}_material_classes.png')
    weight=ndimage.gaussian_filter(pad(hair.astype(float),cov),.6);R.write_mask([weight],T/f'{prefix}_region_mask.png',size=N)
    materials.append({'base':'ClericHead_A' if prefix.endswith('head') else 'Cleric_A','prefix':'ClericHead' if prefix.endswith('head') else 'Cleric','mask':f'{prefix}_region_mask.png','regions':['hair'],'ramps':ramps(base,hair,hair_indices,'m460_c')})
    counts[prefix]={str(i):int((classes==i).sum()) for i in np.unique(classes)}
# The simple rigid shaft retains its projected master paint; only its green shaft changes tier.
staff=np.asarray(Image.open(T/'props/staff_basecolor.png').convert('RGB'),float)/255
h,s,v=hsv(staff);green=(h>75)&(h<175)&(s>.25)&(v>.06);gold=(h>23)&(h<70)&(s>.3);mr=np.zeros_like(staff);mr[:]=[.15,.65,0];mr[green]=[.4,.48,0];mr[gold]=[1,.43,0]
save(staff,T/'m460_staff_basecolor.png');save(np.broadcast_to([.5,.5,1],staff.shape),T/'m460_staff_normal.png');save(mr,T/'m460_staff_metal_rough.png')
mask=np.zeros((*green.shape,4));mask[...,0]=ndimage.gaussian_filter(green.astype(float),.5);mask[...,3]=1;save(mask,T/'m460_staff_region_mask.png')
materials.append({'base':'ClericStaff_A','prefix':'ClericStaff','mask':'m460_staff_region_mask.png','regions':['shaft'],'ramps':ramps(staff,green,staff_indices,'m460_a')})
# The merged head and body share one lookup domain for their continuous hair region.
materials[1]['ramps'] = materials[0]['ramps']
(T/'m460_ramps.json').write_text(json.dumps({'variants':list(pals),'materials':materials},indent=2)+'\n')
report={'native_hair_indices':hair_indices.tolist(),'native_staff_indices':staff_indices.tolist(),'native_source':'m460Sa0.bmp; hair crop [115,68,141,116], staff crop [70,67,92,245], only palette changes >4/255','material_counts':counts,'normal_maps':normal_reports,'specular_channel':'MR.R; openyamm_specular_mask; metallic zero','head_region':'Face/eyes/upper scalp in HeadUV; lower hair remains in body UV and has its own identical native palette ramp.'}
(T/'composition_report.json').write_text(json.dumps(report,indent=2)+'\n');print('TEXTURES',json.dumps(report),flush=True)
