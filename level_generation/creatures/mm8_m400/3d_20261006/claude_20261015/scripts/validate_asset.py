import sys, json, hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];REPO=P.parents[4]
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,accessor_bytes
path=P/'delivery/mm8_lizardman_peasant.glb';d,b=read_glb(path)
def values(i):
    a=d['accessors'][i];kind={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    return np.frombuffer(accessor_bytes(d,b,i),dtype=kind).reshape(a['count'],-1)
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==40
assert {a['name'] for a in d['animations']}=={'Standing','Walk','Hit','Fidget','Death','Corpse'}
assert len(d['materials'])==1 and len(d['images'])==4
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'meshes':[]}
for mesh in d['meshes']:
    triangles=0;weight_error=0;degenerate=0
    for primitive in mesh['primitives']:
        at=primitive['attributes'];pos=values(at['POSITION']);indices=values(primitive['indices']).reshape(-1,3)
        assert indices.max()<len(pos) and np.isfinite(pos).all()
        for key,index in at.items():assert np.isfinite(values(index)).all(),key
        weights=np.concatenate([values(at[k]) for k in ['WEIGHTS_0','WEIGHTS_1'] if k in at],axis=1)
        joints=np.concatenate([values(at[k]) for k in ['JOINTS_0','JOINTS_1'] if k in at],axis=1)
        assert np.max(np.sum(weights>0,axis=1))<=8 and joints.max()<40
        error=float(np.abs(weights.sum(axis=1)-1).max());assert error<1e-4
        weight_error=max(weight_error,error);triangles+=len(indices)
        tri=pos[indices];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
        degenerate+=int(np.count_nonzero(area<1e-12))
    assert degenerate==0,mesh.get('name')
    report['meshes'].append({'name':mesh.get('name'),'triangles':triangles,'max_weight_sum_error':weight_error,'degenerate_triangles':degenerate})
for animation in d['animations']:
    for sampler in animation['samplers']:
        times=values(sampler['input']).ravel()
        assert times[0]==0 and np.all(np.diff(times)>0)
        assert sampler.get('interpolation','LINEAR') in ['LINEAR','STEP']
(P/'review/asset_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: all eight meshes, skin influences, indices, finite attributes and animation timelines')
