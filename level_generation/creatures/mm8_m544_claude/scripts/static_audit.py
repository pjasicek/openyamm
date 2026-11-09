"""Validate the delivered geometry, shared textures, native provenance and nine action durations."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
path=P/'export/mm8_m544.glb';d,b=read_glb(path)
counts={};max_weight=0
for mesh in d['meshes']:
    counts[mesh.get('name','')]=sum(d['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
    for prim in mesh['primitives']:
        a=prim['attributes']
        for key,index in a.items():assert np.isfinite(accessor_array(d,b,index)).all(),key
        pos=accessor_array(d,b,a['POSITION']);ix=accessor_array(d,b,prim['indices'])
        assert ix.min()>=0 and ix.max()<len(pos)
        if 'TEXCOORD_0' in a:
            uv=accessor_array(d,b,a['TEXCOORD_0']);assert uv.min()>=-1e-5 and uv.max()<=1.00001
        if 'WEIGHTS_0' in a:
            w=accessor_array(d,b,a['WEIGHTS_0']);assert np.max(abs(w.sum(1)-1))<1e-5
            max_weight=max(max_weight,int((w>1e-6).sum(1).max()));assert 'WEIGHTS_1' not in a
assert max_weight<=4 and len(d['skins'])==1 and len(d['images'])==5
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['unicorn']
expected=json.loads((P/'work/animation_report.json').read_text())
assert {a['name'] for a in d['animations']}==set(expected)
for action in d['animations']:
    end=max(float(accessor_array(d,b,s['input']).max()) for s in action['samplers'])
    assert abs(end-expected[action['name']]['duration'])<1e-5
    for sampler in action['samplers']:assert np.isfinite(accessor_array(d,b,sampler['output'])).all()
for name in ['Head','HornTip','Breath','FrontHoof_L','FrontHoof_R','HindHoof_L','HindHoof_R','Tail5']:
    assert any(n.get('name')==name for n in d['nodes']),name
native=json.loads((P.parent/'mm8_m544/sources.json').read_text())
for rec in native['sources'].values():
    assert hashlib.sha256((P.parents[2]/rec['path']).read_bytes()).hexdigest()==rec['sha256']
for rec in native['palette_sources'].values():
    assert hashlib.sha256((P.parents[2]/rec['path']).read_bytes()).hexdigest()==rec['sha256']
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
        'triangles_by_mesh':counts,'max_influences':max_weight,'clips':expected,
        'native_frames_verified_unchanged':len(native['sources']),'palette':544}
(P/'review/static_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
