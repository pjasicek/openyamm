"""Verify the retexture return and compose one PBR set on the retained, independently split glow master."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path[:0] = [str(ROOT/'tools'),str(P.parent/'hes_turrets_claude/scripts')]
from merge_head_material import read_glb, write_glb, accessor_array
from normal_map_convention import measure
from raster import rasterise

S = P/'meshy/ion_cannon_retexture_v1'
T = P/'textures'
T.mkdir(exist_ok=True)


def corners(path):
    doc, binary = read_glb(path)
    p = doc['meshes'][0]['primitives'][0]
    ids = accessor_array(doc,binary,p['indices']).reshape(-1,3)
    return [accessor_array(doc,binary,p['attributes'][key])[ids].astype(float) for key in ('POSITION','TEXCOORD_0')]


def add_image(doc, binary, name):
    raw = (T/f'ion_cannon_{name}.png').read_bytes()
    binary.extend(b'\0'*(-len(binary)%4))
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(raw)})
    binary.extend(raw)
    doc['images'].append({'name':'IonCannon_'+name,'mimeType':'image/png','bufferView':len(doc['bufferViews'])-1})
    doc['textures'].append({'source':len(doc['images'])-1,'sampler':0})
    return len(doc['textures'])-1


def main():
    upload = P/'work/ion_cannon_neutral_upload.glb'
    assert hashlib.sha256(upload.read_bytes()).hexdigest()=='b273355734aa1593f053e1f8085638c5879f86ffa9e93df69bff9fc7a1c04e6e'
    a,uv = corners(upload);b,returned_uv = corners(S/'model_urls_glb.glb')
    assert len(a)==len(b)==7916
    scale = np.ptp(a,axis=(0,1))/np.ptp(b,axis=(0,1))
    assert np.ptp(scale)<2e-6,scale
    shift = (a.min((0,1))+a.max((0,1)))/2-scale.mean()*(b.min((0,1))+b.max((0,1)))/2
    b=b*scale.mean()+shift
    errors,ids=cKDTree(b.mean(1)).query(a.mean(1))
    assert len(set(ids))==len(a) and errors.max()<1e-5
    delta=np.linalg.norm(a[:,:,None]-b[ids,None],axis=3)
    order=delta.argmin(2)
    assert all(len(set(row))==3 for row in order)
    corner_error=float(delta.min(2).max())
    uv_error=float(abs(uv-np.take_along_axis(returned_uv[ids],order[:,:,None],axis=1)).max())
    assert corner_error<1e-5 and uv_error<1e-7,(corner_error,uv_error)
    record={'source_sha256':hashlib.sha256((S/'model_urls_glb.glb').read_bytes()).hexdigest(),
            'triangles':len(a),'uniform_rescale':float(scale.mean()),'shift_metres':shift.tolist(),
            'maximum_corner_error_metres':corner_error,'maximum_uv_error_texels_2k':uv_error*2048,
            'decision':'Keep the checked master geometry/normals/UVs; apply the external PNG maps.'}
    raw=np.load(P/'work/ion_cannon_uv_triangles.npz')
    co=raw['positions'];n=np.cross(co[:,1]-co[:,0],co[:,2]-co[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    tri,_=rasterise(raw['uv'],co,n,2048);cover=tri>=0
    load=lambda name:np.asarray(Image.open(S/f'texture_urls_0_{name}.png').convert('RGB'),np.float32)/255
    base=load('base_color');normal=load('normal');rough=load('roughness')[:,:,0]
    r,g,b=np.moveaxis(base,-1,0)
    purple=(b>g*1.12)&(r>g*1.05)
    ivory=(~purple)&(b>r*.62)&(g>r*.78)
    gold=(~purple)&(~ivory)&(r>b*1.18)&(g>b*1.10)
    # Preserve art once; assign material response per texel, with no emission in the opaque atlas.
    specular=np.where(ivory,.55,np.where(gold,.85,.30))
    rough=np.maximum(rough,np.where(ivory,.56,np.where(gold,.42,.64)))
    metallic=np.where(gold,.85,0)
    orm=np.stack((specular,rough,metallic),-1)
    labels=np.where(ivory,5,np.where(gold,9,11)).astype(np.uint8)
    _,near=distance_transform_edt(~cover,return_indices=True)
    base=base[tuple(near)];normal=normal[tuple(near)];orm=orm[tuple(near)]
    correlation=measure(np.asarray(Image.open(S/'texture_urls_0_normal.png')))
    flipped=correlation<=-.15
    if flipped:normal[:,:,1]=1-normal[:,:,1]
    for name,array,size in [('basecolor',base,2048),('normal',normal,1024),('orm',orm,1024)]:
        pixels=np.uint8(np.clip(array,0,1)*255+.5)
        Image.fromarray(pixels).resize((size,size),Image.Resampling.LANCZOS).save(T/f'ion_cannon_{name}.png')
    labels[~cover]=0
    Image.fromarray(labels).resize((1024,1024),Image.Resampling.NEAREST).save(T/'ion_cannon_material_classes.png')
    record.update(normal_source_correlation=correlation,normal_y_flipped=flipped,
        material_classes={'5':'ivory ceramic','9':'gold trim','11':'violet resin'},
        orm_red='Specular mask; no occlusionTexture. Ivory/gold/resin roughness floors 0.56/0.42/0.64.',
        textures={'basecolor':2048,'normal':1024,'orm':1024},colour_variants='One approved palette; seven emission states share all image bytes.')
    doc,binary=read_glb(P/'work/ion_cannon_zones.glb')
    primitives=[copy.deepcopy(m['primitives'][0]) for m in doc['meshes']]
    doc['meshes']=[{'name':'IonCannon','primitives':primitives}]
    doc['nodes']=[{'name':'IonCannon','mesh':0}];doc['scenes']=[{'nodes':[0]}];doc['scene']=0
    doc['images']=[];doc['textures']=[];doc['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]
    textures={key:add_image(doc,binary,key) for key in ('basecolor','normal','orm')}
    for material in doc['materials']:
        name=material['name']
        if name=='Opaque':
            material['pbrMetallicRoughness']={'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':textures['basecolor']},
                'metallicFactor':1,'roughnessFactor':1,'metallicRoughnessTexture':{'index':textures['orm']}}
            material['normalTexture']={'index':textures['normal'],'scale':1}
            material['extras']={'openyamm_specular_mask':True,'openyamm_specular':1,'openyamm_edge_darkening':0}
        else:
            material['pbrMetallicRoughness']={'baseColorFactor':[.03,.01,.06,1],'metallicFactor':0,'roughnessFactor':.25}
            material['emissiveFactor']=[.24,.08,.46]
            material['extensions']={'KHR_materials_emissive_strength':{'emissiveStrength':2}}
            material['extras']={'openyamm_bloom':True,'openyamm_edge_darkening':0}
        material['doubleSided']=False
    doc['extensionsUsed']=['KHR_materials_emissive_strength']
    write_glb(P/'work/ion_cannon_lod0.glb',doc,binary)
    (P/'review/texture_return.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
