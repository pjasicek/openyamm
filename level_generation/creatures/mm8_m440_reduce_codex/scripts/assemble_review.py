"""Attach the unchanged club to its runtime socket for the before/after viewer."""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb
body, prop, out = map(Path, sys.argv[1:])
d,b = read_glb(body); b=bytearray(b)
s,payload = read_glb(prop); s=copy.deepcopy(s)
assert s['nodes']==[{'name':'Club','mesh':0}]
assert d['extensions']['KHR_materials_variants']==s['extensions']['KHR_materials_variants']
off={k:len(d.get(k,[])) for k in ('bufferViews','accessors','images','textures','samplers','materials','meshes')}
b.extend(b'\0'*(-len(b)%4)); start=len(b); b.extend(payload)
for v in s['bufferViews']: v['byteOffset']=v.get('byteOffset',0)+start
for a in s['accessors']: a['bufferView']+=off['bufferViews']
for im in s['images']: im['bufferView']+=off['bufferViews']
for tex in s['textures']:
    tex['source']+=off['images']
    if 'sampler' in tex:tex['sampler']+=off['samplers']
def textures(value):
    for k,v in value.items():
        if isinstance(v,dict):
            if k.endswith('Texture'):v['index']+=off['textures']
            else:textures(v)
for material in s['materials']:textures(material)
for mesh in s['meshes']:
    for prim in mesh['primitives']:
        prim['indices']+=off['accessors']
        prim['attributes']={k:v+off['accessors'] for k,v in prim['attributes'].items()}
        prim['material']+=off['materials']
        for mapping in prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
            mapping['material']+=off['materials']
    for k in ('openyamm_lods','openyamm_shadow_lods'):
        if k in mesh.get('extras',{}):mesh['extras'][k]=[i+off['meshes'] for i in mesh['extras'][k]]
for k in off:d.setdefault(k,[]).extend(s.get(k,[]))
socket=next(n for n in d['nodes'] if n.get('name')=='Club')
socket.setdefault('children',[]).append(len(d['nodes']))
d['nodes'].append({'name':'Club_attachment','mesh':off['meshes']})
d['extensionsUsed']=sorted(set(d.get('extensionsUsed',[]))|set(s.get('extensionsUsed',[])))
write_glb(out,d,b)
