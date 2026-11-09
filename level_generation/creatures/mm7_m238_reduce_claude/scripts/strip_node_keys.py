#!/usr/bin/env python3
"""Drop the collapsed-mesh node keys (scale channels on mesh nodes, written by tools/model_hide_collapsed_meshes.py)
so tools/build_actor_lods.py imports the mesh node as a mesh object; build_export.sh writes them again at the end
with the same tool. Usage: strip_node_keys.py <glb> (in place)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
p = Path(sys.argv[1]); doc, binary = read_glb(p)
mesh_nodes = {i for i, n in enumerate(doc['nodes']) if 'mesh' in n}
dropped = 0
for a in doc.get('animations', []):
    keep = [c for c in a['channels'] if not (c['target'].get('node') in mesh_nodes and c['target']['path'] == 'scale')]
    dropped += len(a['channels']) - len(keep)
    used = sorted({c['sampler'] for c in keep}); remap = {o: n for n, o in enumerate(used)}
    a['samplers'] = [a['samplers'][o] for o in used]
    for c in keep:
        c['sampler'] = remap[c['sampler']]
    a['channels'] = keep
write_glb(p, doc, binary)
print('STRIPPED mesh-node scale channels', dropped)
