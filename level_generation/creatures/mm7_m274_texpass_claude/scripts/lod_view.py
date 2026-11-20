"""Viewer-only GLB that draws one LOD in place of LOD0 (the node's mesh points to that LOD), for LOD-switch checks in
the review viewer. Usage: lod_view.py <glb> <level 1-3> <out glb>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

src, level, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
g = Glb(src)
node = next(n for n in g.doc['nodes'] if n.get('name') == 'M274' and 'mesh' in n)
node['mesh'] = g.doc['meshes'][node['mesh']]['extras']['openyamm_lods'][level - 1]
g.save(out)
print('LOD VIEW', out)
