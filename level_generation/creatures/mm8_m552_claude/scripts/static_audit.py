"""Validate the final Thunderbird geometry, shared textures, skin, action set and texture-return correspondence."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
path=P/'export/mm8_m552.glb'
d,b=read_glb(path)
counts=[]
max_weight=0
for mesh in d['meshes']:
    counts.append(sum(d['accessors'][p['indices']]['count']//3 for p in mesh['primitives']))
    for p in mesh['primitives']:
        a=p['attributes']
        for key,index in a.items():
            assert np.isfinite(accessor_array(d,b,index)).all(),key
        pos=accessor_array(d,b,a['POSITION'])
        ix=accessor_array(d,b,p['indices'])
        assert ix.min()>=0 and ix.max()<len(pos)
        if 'WEIGHTS_0' in a:
            weights=accessor_array(d,b,a['WEIGHTS_0'])
            assert np.max(abs(weights.sum(1)-1))<1e-5
            max_weight=max(max_weight,int((weights>1e-6).sum(1).max()))
            assert 'WEIGHTS_1' not in a
assert max_weight<=4 and counts[0]==11448 and all(.4 < counts[i+1]/counts[i] < .6 for i in range(3)),counts
assert len(d['skins'])==1 and len(d['images'])==4
assert len(d['meshes'][0]['primitives'])==1
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m552_a','m552_b','m552_c']
expected=json.loads((P/'work/clip_manifest.json').read_text())
expected.pop('Stress',None)
assert {a['name'] for a in d['animations']}==set(expected)
for action in d['animations']:
    end=max(float(accessor_array(d,b,s['input']).max()) for s in action['samplers'])
    assert abs(end-expected[action['name']]['seconds'])<1e-5
    for sampler in action['samplers']:
        assert np.isfinite(accessor_array(d,b,sampler['output'])).all()
for name in ['Head','HeadSocket','Tail','HandWing_L','HandWing_R','Toe_L_1','Toe_R_1']:
    assert any(n.get('name')==name for n in d['nodes'])
arrays=[]
for f in ['texturing/thunderbird_neutral.glb','meshy/retexture_v1/model_urls_glb.glb']:
    doc,binary=read_glb(P/f);p=doc['meshes'][0]['primitives'][0]
    arrays.append(tuple(accessor_array(doc,binary,p['attributes'][key]) for key in ['POSITION','TEXCOORD_0']))
t,tu=arrays[0];s,su=arrays[1]
scale=np.ptp(t,axis=0).max()/np.ptp(s,axis=0).max()
s=s*scale+(t.min(0)+t.max(0))/2-(s.min(0)+s.max(0))/2*scale
distance,_=cKDTree(np.c_[s,su]).query(np.c_[t,tu])
missing=distance>1e-5
assert missing.mean()<.01
assert missing.sum() == 38, int(missing.sum())
report=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,
    triangles_by_mesh=counts,max_influences=max_weight,clips=expected,
    texture_return=dict(matched_vertices=int((~missing).sum()),total_vertices=len(t),
        foot_cut_and_wing_vertices_removed_by_meshy=int(missing.sum()),
        treatment='Retain all original geometry and UVs; returned maps cover surrounding foot and wing surfaces.'))
(P/'review/static_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('STATIC AUDIT',counts,max_weight,'influences;',int((~missing).sum()),'texture vertices matched')
