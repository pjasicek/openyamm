"""Grade only the red/blue region ramps; retain the accepted v6 geometry, clips and shared maps."""
import copy
import hashlib
import json
import runpy
import sys
from pathlib import Path
import numpy as np

P=Path(__file__).resolve().parents[1]
BASE=P/'work/before_palette_v7'
OUT=P/'review/palette_v7'
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as rv
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import accessor_array
W=np.array([.2126,.7152,.0722])

def smoothstep(lo,hi,x):
    u=np.clip((x-lo)/(hi-lo),0,1)
    return u*u*(3-2*u)

def grade(colors,part,tier,region):
    rgb=np.array(colors,float);lum=rgb@W
    wing=part=='DragonWings_A'
    if wing:
        factor=1-.09*smoothstep(.015,.10,lum)*(1-smoothstep(.35,.65,lum))
        saturation=1.025 if tier=='cdr1_a' and region==0 else 1.0
    else:
        gain=(.69 if tier=='cdr1_a' else .65) if region==0 else .79
        contrast=np.clip((np.maximum(lum,.001)/.20)**.12,.78,1.25)
        factor=gain*contrast
        recovery=smoothstep(.28,.68,lum)
        factor=factor*(1-recovery)+recovery
        saturation=1.075 if tier=='cdr1_a' and region==0 else 1.0
    out=np.clip((lum[:,None]+(rgb-lum[:,None])*saturation)*factor[:,None],0,1)
    assert np.all(np.isfinite(out)) and np.all(np.diff(out@W)>=-1e-6)
    assert np.all(out[0]==rgb[0])
    return out.tolist()

cfg=json.loads((BASE/'textures/cdr1_ramps.json').read_text())
for material in cfg['materials']:
    for tier in ('cdr1_a','cdr1_b'):
        for region,ramp in enumerate(material['ramps'][tier]):
            ramp['colors']=grade(ramp['colors'],material['base'],tier,region)
(P/'textures/cdr1_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
old,raw=rv.read_glb(BASE/'export/mm6_cdr1.glb');doc=copy.deepcopy(old)
for material in cfg['materials']:
    for tier in ('cdr1_a','cdr1_b'):
        name=material['prefix']+'_'+tier[-1].upper()
        target=next(m for m in doc['materials'] if m['name']==name)
        target['extras']['openyamm_region_ramps']=copy.deepcopy(material['ramps'][tier])
# These six material fields are the whole production change, including every LOD.
restored=copy.deepcopy(doc)
for previous,current in zip(old['materials'],restored['materials']):
    current['extras']['openyamm_region_ramps']=previous['extras']['openyamm_region_ramps']
assert restored==old
assert sum(a!=b for a,b in zip(old['materials'],doc['materials']))==6
assert all(a==b for a,b in zip(old['materials'],doc['materials']) if a['name'].endswith('_C'))
rv.write_glb(P/'export/mm6_cdr1.glb',doc,raw)
check,checkraw=rv.read_glb(P/'export/mm6_cdr1.glb');assert bytes(raw)==bytes(checkraw)
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')

# Keep all mesh/skin/animation and non-colour image data identical in the viewer exports.
def accessors(doc,data):
    values={}
    for mesh in doc['meshes']:
        for i,primitive in enumerate(mesh['primitives']):
            for key,index in dict(primitive['attributes'],indices=primitive['indices']).items():
                values[(mesh['name'],i,key)]=accessor_array(doc,data,index).tobytes()
    for skin in doc['skins']:
        values[('skin',skin.get('name'))]=([doc['nodes'][i]['name'] for i in skin['joints']],accessor_array(doc,data,skin['inverseBindMatrices']).tobytes())
    for animation in doc['animations']:
        for channel in animation['channels']:
            target=channel['target'];sampler=animation['samplers'][channel['sampler']]
            key=(animation['name'],doc['nodes'][target['node']]['name'],target['path'])
            values[key]=(sampler.get('interpolation','LINEAR'),*[accessor_array(doc,data,sampler[k]).tobytes() for k in ('input','output')])
    return values
def image_bytes(doc,data,index):
    v=doc['bufferViews'][doc['images'][index]['bufferView']];start=v.get('byteOffset',0)
    return bytes(data[start:start+v['byteLength']])
report={}
for tier in 'abc':
    name=f'mm6_cdr1_{tier}.glb';prior,priorraw=rv.read_glb(BASE/'review/viewer'/name)
    current,currentraw=rv.read_glb(P/'review/viewer'/name)
    assert accessors(prior,priorraw)==accessors(current,currentraw),name
    changed={current['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source'] for m in current['materials']}
    if tier=='c':changed=set()
    for i in range(len(prior['images'])):
        if i not in changed:assert image_bytes(prior,priorraw,i)==image_bytes(current,currentraw,i),(name,i)
    current,currentraw=rv._compact(current,currentraw)
    rv.write_glb(P/'review/viewer'/name,current,currentraw)
    report[tier]={'all_geometry_skin_animation_accessors_unchanged':True,'all_non_colour_maps_unchanged':True,'gold_all_images_unchanged':tier=='c'}
manifest=json.loads((P/'review/viewer/manifest.json').read_text());manifest['revision']='v7-palette-depth'
for model in manifest['models']:
    name=model['url'].split('?')[0];sha=hashlib.sha256((P/'review/viewer'/name).read_bytes()).hexdigest()
    model.update(url=name+'?v='+sha[:12],sha256=sha,revision=manifest['revision'])
(P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report.update(production_binary_unchanged=True,production_change='Six red/blue material region-ramp fields only',gold_materials_unchanged=True,all_shared_maps_unchanged=True)
(OUT/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Updated six red/blue material ramps; preserved all geometry, animations, images and gold materials')
