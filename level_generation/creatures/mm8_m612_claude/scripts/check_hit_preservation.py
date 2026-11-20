"""Confirm the final timing repair did not alter any other clip, mesh, bind or image."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(P.parent/'claude_shared')]
from region_variants import read_glb
from build_actor_lods import accessor_bytes
def parts(path):
    d,b=read_glb(path);clips={}
    for a in d['animations']:
        h=hashlib.sha256()
        for c in a['channels']:
            t=c['target'];s=a['samplers'][c['sampler']]
            h.update(json.dumps([d['nodes'][t['node']]['name'],t['path'],s.get('interpolation','LINEAR')]).encode())
            for v in ('input','output'):h.update(accessor_bytes(d,b,s[v]))
        clips[a['name']]=h.hexdigest()
    h=hashlib.sha256()
    for m in d['meshes']:
        for p in m['primitives']:
            for name,i in sorted(p['attributes'].items()):h.update(name.encode()+accessor_bytes(d,b,i))
            h.update(accessor_bytes(d,b,p['indices']))
    for s in d['skins']:h.update(accessor_bytes(d,b,s['inverseBindMatrices']))
    for i in d['images']:
        v=d['bufferViews'][i['bufferView']];off=v.get('byteOffset',0);h.update(b[off:off+v['byteLength']])
    return {'clips':clips,'geometry_bind_images':h.hexdigest()}
old=parts(ROOT/'assets_source/worlds/mm8/models/mm8_m612.glb');new=parts(P/'export/mm8_m612.glb')
assert old['geometry_bind_images']==new['geometry_bind_images']
for name,h in old['clips'].items():
    assert (h==new['clips'][name]) == (name!='Hit'),name
report={'before':old,'after':new,'only_changed_clip':'Hit','mesh_bind_and_images_identical':True}
(P/'work/hit_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PRESERVATION: only Hit changed; eight other clips, all LOD meshes, bind and images identical')
