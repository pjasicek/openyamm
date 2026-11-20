"""Check the delivered school geometry, material sharing, native bindings and installed source."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,accessor_array
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d,b=read_glb(P/'export/mm8_m636.glb');report={'meshes':[]}
visible=[n for n in d['nodes'] if 'mesh' in n];assert len(visible)==1 and visible[0]['name']=='School'
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==61
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m636_a','m636_b','m636_c']
assert len(d['images'])==4 and len(d['materials'])==3
for m in d['materials']:
    assert m['alphaMode']=='OPAQUE' and m['pbrMetallicRoughness']['metallicFactor']==0
    assert m['extras']['openyamm_specular_mask'] and len(m['extras']['openyamm_region_ramps'])==1
for mesh in d['meshes']:
    assert len(mesh['primitives'])==1
    pr=mesh['primitives'][0];a=pr['attributes'];points=accessor_array(d,b,a['POSITION']);uv=accessor_array(d,b,a['TEXCOORD_0']);w=accessor_array(d,b,a['WEIGHTS_0']);indices=accessor_array(d,b,pr['indices']).reshape(-1,3)
    xyz=points[indices];coords=uv[indices];area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
    u,v=coords[:,1]-coords[:,0],coords[:,2]-coords[:,0];uvarea=np.abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])/2
    assert np.isfinite(points).all() and area.min()>1e-12 and uvarea.min()>1e-10
    assert np.all((uv>=0)&(uv<=1)) and abs(w.sum(1)-1).max()<1e-6
    influences=int(np.count_nonzero(w>1e-5,axis=1).max());assert influences<=4
    report['meshes'].append({'name':mesh['name'],'triangles':len(indices),'vertices':len(points),'max_influences':influences,'degenerate_geometry':0,'degenerate_uv':0})
assert [m['triangles'] for m in report['meshes']]==[7800,3888,1908,924]
report['clips']={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
assert report['clips']=={'Dead':1,'Death':1.25,'Swim':1.875}
manifest=yaml.safe_load((R/'assets_dev/worlds/mm8/models/actors.yml').read_text())
entries=manifest if isinstance(manifest,list) else manifest['actors']
fish=[e for e in entries if e.get('model')=='worlds/mm8/models/mm8_m636.glb'];assert len(fish)==3
assert {e['skin'] for e in fish}=={'m636_a','m636_b','m636_c'}
for entry in fish:
    assert entry['scale']==100 and entry['z_offset']==22 and 'scale_reference' not in entry
    assert entry['clips']['dying']=='Death' and entry['clips']['dead']=='Dead'
    assert all(entry['clips'][role]=='Swim' for role in ['standing','walking','hit','fidget','attack_melee','attack_ranged'])
report['bindings']=fish
report['export_sha256']=sha(P/'export/mm8_m636.glb')
assert report['export_sha256']==sha(R/'assets_source/worlds/mm8/models/mm8_m636.glb')
report['runtime_sha256']=sha(R/'assets_dev/worlds/mm8/models/mm8_m636.glb')
runtime,_=read_glb(R/'assets_dev/worlds/mm8/models/mm8_m636.glb');assert len(runtime['animations'])==3
report['runtime_images']=[i.get('uri') for i in runtime['images']]
assert all((R/'assets_dev/worlds/mm8/models'/uri).exists() for uri in report['runtime_images'])
(P/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n');print('VALIDATED',report['export_sha256'],[m['triangles'] for m in report['meshes']])
