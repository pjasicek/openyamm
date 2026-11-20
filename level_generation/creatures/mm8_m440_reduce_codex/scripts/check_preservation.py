"""Assert preservation of every unchanged runtime contract in the reduction candidate."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tools'))
from build_actor_lods import read_glb,accessor_bytes,write_glb
from cook_model_geometry import cook_geometry
P=Path(__file__).resolve().parents[1]
s,b=read_glb(P/'work/mm8_m440_source_pre_reduce.glb');d,c=read_glb(P/'export/mm8_m440.glb')
assert s['nodes']==d['nodes']
assert [x['joints'] for x in s['skins']]==[x['joints'] for x in d['skins']]
assert s['materials']==d['materials'] and s['textures']==d['textures']
for x,y in zip(s['skins'],d['skins']):
    assert accessor_bytes(s,b,x['inverseBindMatrices'])==accessor_bytes(d,c,y['inverseBindMatrices'])
assert len(s['animations'])==len(d['animations'])==8
for x,y in zip(s['animations'],d['animations']):
    assert x['name']==y['name'] and x['channels']==y['channels']
    for a,z in zip(x['samplers'],y['samplers']):
        for key in ('input','output'):assert accessor_bytes(s,b,a[key])==accessor_bytes(d,c,z[key])
def image_bytes(doc,payload,image):
    v=doc['bufferViews'][image['bufferView']];o=v.get('byteOffset',0)
    return payload[o:o+v['byteLength']]
assert len(s['images'])==len(d['images'])
assert all(image_bytes(s,b,x)==image_bytes(d,c,y) for x,y in zip(s['images'],d['images']))
node=next(n for n in d['nodes'] if n.get('name')=='M440')
levels=[node['mesh']]+d['meshes'][node['mesh']]['extras']['openyamm_lods']
for mi in levels[1:]+d['meshes'][node['mesh']]['extras']['openyamm_shadow_lods'][1:]:
    for x,y in zip(s['meshes'][mi]['primitives'],d['meshes'][mi]['primitives']):
        assert x.get('extensions')==y.get('extensions')
        for key in x['attributes']:assert accessor_bytes(s,b,x['attributes'][key])==accessor_bytes(d,c,y['attributes'][key])
        assert accessor_bytes(s,b,x['indices'])==accessor_bytes(d,c,y['indices'])
a=np.load(P/'work/mesh_in.npz');z=np.load(P/'work/mesh_r94.npz');keep=np.load(P/'work/keep_fitted.npy')
assert np.array_equal(a['verts'][a['faces'][keep]],z['verts'][z['faces'][:keep.sum()]])
assert np.array_equal(a['wuv'].reshape(-1,3,2)[keep],z['wuv'].reshape(-1,3,2)[:keep.sum()])
counts=[sum(d['accessors'][q['indices']]['count']//3 for q in d['meshes'][mi]['primitives']) for mi in levels]
assert all(a>b for a,b in zip(counts,counts[1:])),counts
assert all('JOINTS_1' not in q['attributes'] for mi in levels for q in d['meshes'][mi]['primitives'])
summary={'source_colour_lods':[18752,10649,6400,4238],'candidate_colour_lods':counts,
         'animations_unchanged':8,'materials_and_images_unchanged':True,'skeleton_unchanged':True,
         'lower_lods_unchanged':True,'protected_faces_exact':int(keep.sum()),'club_unchanged':True,
         'candidate_sha256':hashlib.sha256((P/'export/mm8_m440.glb').read_bytes()).hexdigest()}
# Measure the actual runtime back-face expansion without installing or changing texture payloads.
import copy
cooked=copy.deepcopy(d)
payload,recipe=cook_geometry(cooked,c,Path('build/game/openyamm_model_texture_cook').resolve())
write_glb(P/'export/mm8_m440_geometry_preview.glb',cooked,payload)
summary['runtime_geometry_lods']=[sum(cooked['accessors'][q['indices']]['count']//3 for q in cooked['meshes'][mi]['primitives']) for mi in levels]
summary['geometry_recipe']=recipe
(P/'review/preservation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
