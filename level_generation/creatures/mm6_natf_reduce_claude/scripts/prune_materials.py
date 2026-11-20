"""Drop materials no primitive or KHR_materials_variants mapping references (natf: the installed per-LOD texture sets
L1-L3, unused once tools/build_actor_lods.py rebuilt every LOD on the LOD0 material), then their textures and images,
and the buffer views only those images used. Usage: prune_materials.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, out = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src)
prims = [p for m in doc['meshes'] for p in m['primitives']]
maps = [mp for p in prims for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])]
used = sorted({p['material'] for p in prims if 'material' in p} | {mp['material'] for mp in maps})
mmap = {old: new for new, old in enumerate(used)}
doc['materials'] = [doc['materials'][i] for i in used]
for p in prims:
    if 'material' in p:
        p['material'] = mmap[p['material']]
for mp in maps:
    mp['material'] = mmap[mp['material']]


def texture_refs(node):
    """Every {'index': n} texture-info dict below a material."""
    if isinstance(node, dict):
        if 'index' in node and isinstance(node['index'], int) and ('texCoord' in node or len(node) <= 4):
            yield node
        for k, v in node.items():
            if k != 'index':
                yield from texture_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from texture_refs(v)


refs = list(texture_refs(doc['materials']))
used_tex = sorted({r['index'] for r in refs})
tmap = {old: new for new, old in enumerate(used_tex)}
doc['textures'] = [doc['textures'][i] for i in used_tex]
for r in refs:
    r['index'] = tmap[r['index']]
used_img = sorted({t['source'] for t in doc['textures']})
imap = {old: new for new, old in enumerate(used_img)}
doc['images'] = [doc['images'][i] for i in used_img]
for t in doc['textures']:
    t['source'] = imap[t['source']]
# compact buffer views: those of accessors and remaining images
views = sorted({a['bufferView'] for a in doc['accessors'] if 'bufferView' in a} | {im['bufferView'] for im in doc['images']})
vmap, newbin, nviews = {}, bytearray(), []
for new, old in enumerate(views):
    v = dict(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); nviews.append(v); vmap[old] = new
doc['bufferViews'] = nviews
for a in doc['accessors']:
    if 'bufferView' in a:
        a['bufferView'] = vmap[a['bufferView']]
for im in doc['images']:
    im['bufferView'] = vmap[im['bufferView']]
write_glb(out, doc, bytes(newbin))
print('PRUNED materials', len(used), 'textures', len(used_tex), 'images', len(used_img), f'{len(newbin) / 1e6:.1f} MB')
