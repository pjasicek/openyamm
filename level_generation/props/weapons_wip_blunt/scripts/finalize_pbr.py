"""Convert embedded maps to PNG, bound albedo, and make physical metallic masks explicit."""
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
import normal_map_convention
from prepare_actor_glb import omit_mesh_nodes
sys.path.insert(0,str(P.parents[2]/'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import array


def shaft_texels(d,b):
    """Rasterize actual UV triangles to their physical length coordinate for authored material regions."""
    result=np.full((1024,1024),-1.,np.float32)
    all_points=[array(d,b,p['attributes']['POSITION']) for m in d['meshes'] for p in m['primitives']]
    z=np.concatenate(all_points)[:,2];low,high=z.min(),z.max()
    for mesh in d['meshes']:
        for primitive in mesh['primitives']:
            points=array(d,b,primitive['attributes']['POSITION'])
            uv=array(d,b,primitive['attributes']['TEXCOORD_0'])*[1023,-1023]+[0,1023]
            indices=array(d,b,primitive['indices']).reshape(-1,3)
            for tri in indices:
                a,c,e=uv[tri];lo=np.maximum(np.floor(np.minimum(np.minimum(a,c),e)).astype(int),0)
                hi=np.minimum(np.ceil(np.maximum(np.maximum(a,c),e)).astype(int),1023)
                yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];pixel=np.stack([xx,yy],-1)
                u,v=c-a,e-a;den=u[0]*v[1]-u[1]*v[0]
                if abs(den)<1e-8:continue
                delta=pixel-a;w1=(delta[:,:,0]*v[1]-delta[:,:,1]*v[0])/den
                w2=(u[0]*delta[:,:,1]-u[1]*delta[:,:,0])/den;w0=1-w1-w2
                inside=(w0>=-1e-4)&(w1>=-1e-4)&(w2>=-1e-4)
                height=(high-(w0*points[tri[0],2]+w1*points[tri[1],2]+w2*points[tri[2],2]))/(high-low)
                result[yy[inside],xx[inside]]=height[inside]
    assert (result>=0).any()
    return result


def nonmetal_regions(icon,rgb,along):
    r,g,b=[rgb[:,:,i].astype(float) for i in range(3)]
    warm=(r>g*1.32)&(g>b*1.10)
    red=(r>g*1.6)&(r>b*1.5)
    ivory=(r>130)&(g>125)&(b>105)&(abs(r-g)<32)&(abs(g-b)<35)
    dark=(r<85)&(g<85)&(b<85)
    teal=(g>r*1.08)&(b>r*1.08)
    mask=np.zeros(along.shape,bool)
    if icon in ['7item050','item066','hammer2','club3','item078']:
        mask|=(along<.76)&(warm|red|dark)
    if icon in ['item075','mace3','item249']:
        mask|=(along<.79)&(ivory|dark|red)
    if icon in ['item068','item340']:
        mask|=(along<.70)&(warm|ivory|dark)
    if icon=='7item052':mask|=(along<.72)&(teal|dark)
    if icon=='item070':mask|=(along<.48)&dark
    if icon in ['6hammer4','hammer3','mace4','7item232']:
        mask|=(along<.76)&(red|teal)
    return mask&(along>=0)


def finalize(path,wood=False):
    d,b=read_glb(path);payload=bytearray(b);roles={}
    for mat in d['materials']:
        pbr=mat.get('pbrMetallicRoughness',{})
        for key,role in [('baseColorTexture','albedo'),('metallicRoughnessTexture','orm')]:
            if key in pbr:roles[d['textures'][pbr[key]['index']]['source']]=role
        if 'normalTexture' in mat:roles[d['textures'][mat['normalTexture']['index']]['source']]='normal'
    stats={};icon=path.name.removesuffix('_raw.glb');albedo=None
    for n,image in enumerate(d.get('images',[])):
        if roles.get(n)=='albedo':
            view=d['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
            albedo=np.array(Image.open(io.BytesIO(b[offset:offset+view['byteLength']])).convert('RGB').resize((1024,1024)))
    along=shaft_texels(d,b) if not wood else None
    for n,image in enumerate(d.get('images',[])):
        v=d['bufferViews'][image['bufferView']];offset=v.get('byteOffset',0)
        im=Image.open(io.BytesIO(b[offset:offset+v['byteLength']])).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
        a=np.array(im);role=roles.get(n)
        if role=='albedo':a=np.clip(a,30,243)
        if role=='orm':
            a[:,:,0]=255;a[:,:,1]=np.maximum(a[:,:,1],105)
            a[:,:,2]=0 if wood else np.where(a[:,:,2]>128,255,0)
            if not wood:
                corrected=nonmetal_regions(icon,albedo,along)
                a[:,:,2][corrected]=0;a[:,:,1][corrected]=np.maximum(a[:,:,1][corrected],160)
                stats['authored_dielectric_texels']=int(corrected.sum())
            stats['metallic_texels']=int((a[:,:,2]>128).sum());stats['dielectric_texels']=int((a[:,:,2]<128).sum())
        out=io.BytesIO();Image.fromarray(a).save(out,format='PNG');png=out.getvalue()
        payload.extend(b'\0'*(-len(payload)%4));image['bufferView']=len(d['bufferViews']);image['mimeType']='image/png'
        d['bufferViews'].append({'buffer':0,'byteOffset':len(payload),'byteLength':len(png)});payload.extend(png)
    target=path.with_name(path.name.replace('_raw.glb','_export.glb'))
    write_glb(target,d,bytes(payload))
    if 'normal' in roles.values():
        stats['normal_convention']=[list(r) for r in normal_map_convention.convert(target,target,threshold=-.05)]
    compact,body=read_glb(target)
    write_glb(target,compact,omit_mesh_nodes(compact,body,[]))
    stats['image_size']=1024;stats['export']=str(target.relative_to(P))
    (target.with_suffix('.pbr.json')).write_text(json.dumps(stats,indent=2)+'\n')
    return stats


if __name__=='__main__':
    for p in sorted((P/'work/meshy').glob('*_raw.glb')):
        print(p.name,finalize(p,p.name.split('_raw')[0] in ['club1','club2','7item058','item077']))
