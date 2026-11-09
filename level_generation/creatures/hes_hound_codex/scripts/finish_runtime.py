"""Add shared tier ramps and per-tier mouth emission; fit static armour to its carrier joints."""
import copy
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
REPO=PROJECT.parents[2]
sys.path.insert(0,str(PROJECT.parent/'claude_shared'))
sys.path.insert(0,str(REPO/'tools'))
import link_static_model_lods as L
import region_variants as R
OUT=PROJECT/'export'
R.apply_variants(str(PROJECT/'work/hound_lods.glb'),str(PROJECT/'work/hound_variants.glb'),
                 str(PROJECT/'textures/hound_ramps.json'))
doc,binary=R.read_glb(PROJECT/'work/hound_variants.glb')
variants=[v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
for glow_name,gains in [('MawGlow',[.22,.60,1.]),('ThroatFissures',[0.,0.,.55])]:
    glow_i=next(i for i,m in enumerate(doc['materials']) if m['name']==glow_name)
    per={}
    for tier,gain in zip(variants,gains):
        m=copy.deepcopy(doc['materials'][glow_i])
        m['name']=glow_name+'_'+tier
        m['pbrMetallicRoughness']={'baseColorFactor':[0,0,0,1],'metallicFactor':0.,'roughnessFactor':1.}
        m['emissiveFactor']=[gain,.16*gain,.01*gain]
        m['extras']={'openyamm_specular':0.,'openyamm_bloom':True}
        m.pop('emissiveTexture',None)
        per[tier]=len(doc['materials'])
        doc['materials'].append(m)
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if primitive.get('material')==glow_i:
                primitive['material']=per['hound_a']
                primitive.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[
                    {'material':per[t],'variants':[variants.index(t)]} for t in variants]}
for m in doc['materials']:
    m['doubleSided']=False
    if m['name'].startswith('HoundHide'):
        m.setdefault('extras',{}).update(openyamm_specular=1.,openyamm_specular_mask=True)
        m['pbrMetallicRoughness']['metallicFactor']=0.
R.write_glb(PROJECT/'work/hound_variants.glb',doc,binary)

def accessor(d,b,i):
    a=d['accessors'][i]
    v=d['bufferViews'][a['bufferView']]
    off=v.get('byteOffset',0)+a.get('byteOffset',0)
    n={'VEC3':3,'MAT4':16}[a['type']]
    assert a['componentType']==5126 and v.get('byteStride',n*4)==n*4
    return off,np.frombuffer(bytes(b[off:off+a['count']*n*4]),np.float32).reshape(a['count'],n).copy()

skin=doc['skins'][0]
names=[doc['nodes'][j]['name'] for j in skin['joints']]
_,ibms=accessor(doc,binary,skin['inverseBindMatrices'])
info=json.loads((PROJECT/'work/attachments.json').read_text())
for name,entry in info.items():
    path=PROJECT/f'work/attachments_raw/hes_hound_{name}.glb'
    d,b=R.read_glb(path)
    if name.startswith('collar'): L.link(d)
    b=bytearray(b)
    M=ibms[names.index(entry['bone'])].reshape(4,4).T
    done=set()
    for mesh in d['meshes']:
        for pr in mesh['primitives']:
            for key in ['POSITION','NORMAL']:
                i=pr['attributes'][key]
                if i in done:continue
                done.add(i)
                off,a=accessor(d,b,i)
                if key=='POSITION':
                    a=(np.c_[a,np.ones(len(a))]@M.T)[:,:3]
                    d['accessors'][i].update(min=a.min(0).tolist(),max=a.max(0).tolist())
                else:
                    a=a@M[:3,:3].T
                    a/=np.linalg.norm(a,axis=1,keepdims=True)
                b[off:off+a.size*4]=a.astype(np.float32).tobytes()
    for m in d['materials']:
        m['doubleSided']=False
        m.setdefault('extras',{})['openyamm_specular']=1.
    # These broad low-poly pieces keep their silhouette: 22 triangles per back plate, 44 shoulders.
    R.write_glb(OUT/f'hes_hound_{name}.glb',d,b)
    entry['triangles_per_lod']=[sum(d['accessors'][p['indices']]['count']//3 for p in mesh['primitives']) for mesh in d['meshes']]
(OUT/'attachments.json').write_text(json.dumps(info,indent=2)+'\n')
print('Shared variants and six rigid attachments prepared')
