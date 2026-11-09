"""Assert runtime asset limits and retained authored animation data."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
from material_classes_to_orm import accessor
path=P/'export/mm8_m560.glb';d,b=R.read_glb(path)
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m560_a','m560_b','m560_c']
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==44
assert len(d['images'])==4
counts=[];min_area=[]
for mesh in d['meshes']:
    count=0;area=[]
    for p in mesh['primitives']:
        x=accessor(d,b,p['attributes']['POSITION']);uv=accessor(d,b,p['attributes']['TEXCOORD_0']);idx=accessor(d,b,p['indices']).astype(int).ravel()
        w=accessor(d,b,p['attributes']['WEIGHTS_0']);j=accessor(d,b,p['attributes']['JOINTS_0']);n=accessor(d,b,p['attributes']['NORMAL'])
        assert np.isfinite(x).all() and np.isfinite(uv).all() and np.isfinite(n).all()
        assert idx.max()<len(x) and idx.min()>=0 and len(idx)%3==0
        assert np.max(np.abs(w.sum(1)-1))<1e-5 and w.min()>=0 and j.max()<44
        assert 'WEIGHTS_1' not in p['attributes']
        t=x[idx].reshape(-1,3,3);a=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)*.5
        assert (a>1e-12).all(),(mesh['name'],int((a<=1e-12).sum()))
        count+=len(idx)//3;area.extend(a)
    counts.append(count);min_area.append(float(min(area)))
expected={'Fly':1.,'Attack':1.125,'Hit':.875,'Death':.75,'Dead':1.}
durations={};root_travel={}
root=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='Spine1')
for clip in d['animations']:
    times=[accessor(d,b,s['input']) for s in clip['samplers']];duration=max(float(t.max()) for t in times)-min(float(t.min()) for t in times)
    assert abs(duration-expected[clip['name']])<1e-5
    durations[clip['name']]=duration
    channel=next(c for c in clip['channels'] if c['target']=={'node':root,'path':'translation'})
    positions=accessor(d,b,clip['samplers'][channel['sampler']]['output'])
    root_travel[clip['name']]=float(np.ptp(positions[:,1]))
    if clip['name'] in ['Fly','Attack','Hit']:
        assert root_travel[clip['name']]<.0181,('wing-driven vertical lift',clip['name'],root_travel)
assert set(durations)==set(expected)
node=next(n for n in d['nodes'] if n.get('name')=='Wyvern');m=d['meshes'][node['mesh']];levels=[node['mesh']]+m['extras']['openyamm_lods'];tri=[counts[i] for i in levels];assert tri[0]<15000 and all(a>b for a,b in zip(tri,tri[1:]))
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':tri,'mesh_counts':counts,'smallest_triangles':min_area,'bones':44,'max_influences':4,'shared_images':4,'durations':durations,'root_vertical_travel':root_travel,'source_bytes':path.stat().st_size}
(P/'review/delivery_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
