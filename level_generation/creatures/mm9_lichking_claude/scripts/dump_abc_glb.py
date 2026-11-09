"""Print nodes (with parent), skins, clips (name, duration) of a converted MM9 GLB."""
import sys
from pygltflib import GLTF2
import numpy as np
g = GLTF2().load(sys.argv[1])
par = {}
for i, n in enumerate(g.nodes):
    for c in (n.children or []):
        par[c] = i
for i, n in enumerate(g.nodes):
    print(i, n.name, 'parent', g.nodes[par[i]].name if i in par else None, 'T', [round(x, 3) for x in (n.translation or [0, 0, 0])])
print('meshes', [(m.name, len(m.primitives)) for m in g.meshes])
def acc_max(a):
    return g.accessors[a].max
for a in g.animations:
    t = max(acc_max(s.input)[0] for s in a.samplers)
    print('clip', a.name, round(t, 3), 'channels', len(a.channels))
