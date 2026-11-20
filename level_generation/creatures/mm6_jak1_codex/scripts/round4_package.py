"""Package reduced attachment and patch only Staff-weighted primitives in combined review sources."""
import copy, hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]; R=P/'review/round4'; W=P/'work/round4'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb, write_glb, accessor_array, append_accessor, add_image, compact
from split_attachment import split_primitive
levels=[]
for level in range(4):
    d,b=read_glb(W/f'staff_lod{level}.glb')
    node=next(n for n in d['nodes'] if 'mesh' in n)
    assert not any(k in node for k in ['matrix','translation','rotation','scale']),node
    q=d['meshes'][node['mesh']]['primitives'][0]
    attrs={k:accessor_array(d,b,i) for k,i in q['attributes'].items() if k in ['POSITION','NORMAL','TEXCOORD_0']}
    indices=accessor_array(d,b,q['indices']).ravel()
    levels.append((attrs,indices,{k:d['accessors'][i] for k,i in q['attributes'].items()},d['accessors'][q['indices']]))

def maps(doc,binary):
    return {key:add_image(doc,binary,Image.open(P/f'textures/round4_staff/{key}.png'),f'Staff_round4_{key}',0)
            for key in ['basecolor','metal_rough','normal']}
def material(mat,indices):
    mat['pbrMetallicRoughness']['baseColorTexture']['index']=indices['basecolor']
    mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=indices['metal_rough']
    mat['pbrMetallicRoughness']['metallicFactor']=0
    mat['normalTexture']={'index':indices['normal']}
    mat['extras']={'openyamm_specular':1,'openyamm_specular_mask':True}

d,b=read_glb(R/'before/export/mm6_jak1_staff.glb'); textures=maps(d,b)
for mat in d['materials']:material(mat,textures)
for level,(attrs,ix,templates,it) in enumerate(levels):
    q=d['meshes'][level]['primitives'][0]
    q['attributes']={k:append_accessor(d,b,v,templates[k],34962)for k,v in attrs.items()}
    q['indices']=append_accessor(d,b,ix,it,34963)
write_glb(P/'export/mm6_jak1_staff.glb',*compact(d,b))

# Body delivery is deliberately never re-exported. Combined files keep exact body attributes and animation bytes.
for name in ['mm6_jak1_combined.glb','mm6_jak1_lods.glb','mm6_jak1_runtime_lod0.glb']:
    d,b=read_glb(R/'before/export'/name); original=copy.deepcopy(d); original_binary=bytes(b)
    node=next(n for n in d['nodes']if n.get('name')=='Jackalman')
    joints=d['skins'][node['skin']]['joints']; slot=joints.index(next(i for i,n in enumerate(d['nodes'])if n.get('name')=='Staff'))
    inverse=accessor_array(d,b,d['skins'][node['skin']]['inverseBindMatrices'])[slot].reshape(4,4).T
    transform=np.linalg.inv(inverse); tex=maps(d,b)
    for mat in d['materials']:
        if mat['name'].startswith('HookedStaff'):material(mat,tex)
    for mi,mesh in enumerate(d['meshes']):
        level=mi%4; attrs,ix,templates,it=levels[level]
        for q in mesh['primitives']:
            body,staff=split_primitive(d,b,q,slot)
            if not len(staff):continue
            transformed={k:v.copy()for k,v in attrs.items()}
            transformed['POSITION']=(np.c_[attrs['POSITION'],np.ones(len(attrs['POSITION']))]@transform.T)[:,:3]
            normals=attrs['NORMAL']@transform[:3,:3].T
            transformed['NORMAL']=normals/np.linalg.norm(normals,axis=1)[:,None]
            used,body_ix=np.unique(body.ravel(),return_inverse=True)
            old_attrs=q['attributes'].copy()
            for k,ai in old_attrs.items():
                current=accessor_array(d,b,ai); values=np.zeros((len(attrs['POSITION']),current.shape[1]),dtype=current.dtype)
                if k in transformed:values[:]=transformed[k]
                elif k=='JOINTS_0':values[:,0]=slot
                elif k=='WEIGHTS_0':values[:,0]=1
                elif k not in ['JOINTS_1','WEIGHTS_1']:raise ValueError(k)
                merged=np.concatenate([current[used],values]);q['attributes'][k]=append_accessor(d,b,merged,d['accessors'][ai],34962)
                assert np.array_equal(merged[:len(used)],current[used])
            ai=q['indices'];current=accessor_array(d,b,ai)
            new_ix=np.r_[body_ix,ix+len(used)].astype(current.dtype)
            q['indices']=append_accessor(d,b,new_ix,d['accessors'][ai],34963)
    assert d['nodes']==original['nodes'] and d['animations']==original['animations'] and d['skins']==original['skins']
    assert bytes(b[:len(original_binary)])==original_binary
    write_glb(P/'export'/name,d,b)
for name in ['export/mm6_jak1.glb','export/mm6_jak1_body_unmerged.glb','integration/actors.yml','source/mm6_jak1.blend','textures/jak1_ramps_runtime.json']:
    assert (P/name).read_bytes()==(R/'before'/name).read_bytes(),name
print('STAFF PACKAGE PASS', [len(v[1])//3 for v in levels],flush=True)
