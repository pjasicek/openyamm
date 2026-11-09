#!/usr/bin/env python3
"""Shadow chain as the production Air Elemental had it: the body casts its shadow with the colour mesh one level
coarser (shadow LOD0-2 = colour LOD1-3), so the shadow meshes tools/build_actor_lods.py merges are dropped.
Run compact_glb.py afterwards. Usage: shadow_chain.py <in.glb> <out.glb> [mesh node, default Body]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2]); NODE = sys.argv[3] if len(sys.argv) > 3 else 'Body'
doc, binary = read_glb(src)
mesh = doc['meshes'][next(n for n in doc['nodes'] if n.get('name') == NODE and 'mesh' in n)['mesh']]
extras = mesh['extras']; drop = set(extras['openyamm_shadow_lods']) - set(extras['openyamm_lods'])
extras['openyamm_shadow_lods'] = list(extras['openyamm_lods'])
keep = [i for i in range(len(doc['meshes'])) if i not in drop]; remap = {old: new for new, old in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for m in doc['meshes']:
    for key in ('openyamm_lods', 'openyamm_shadow_lods'):
        if key in m.get('extras', {}):
            m['extras'][key] = [remap[i] for i in m['extras'][key]]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = remap[n['mesh']]
print('SHADOW', NODE, 'chain = colour LODs', extras['openyamm_shadow_lods'], 'dropped', len(drop), 'meshes')
write_glb(dst, doc, binary)
