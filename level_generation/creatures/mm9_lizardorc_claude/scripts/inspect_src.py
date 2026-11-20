import sys, numpy as np
from pygltflib import GLTF2
g=GLTF2().load(sys.argv[1])
print('nodes',len(g.nodes)); 
par={}
for i,n in enumerate(g.nodes):
    for c in n.children or []: par[c]=i
for i,n in enumerate(g.nodes):
    print(i,repr(n.name),'p',par.get(i),'mesh' if n.mesh is not None else '', [round(x,3) for x in (n.translation or [])])
print('meshes',[ (m.name,len(m.primitives)) for m in g.meshes])
for m in g.meshes:
  for p in m.primitives:
    print(p.material, g.accessors[p.attributes.POSITION].count, g.accessors[p.indices].count//3, g.accessors[p.attributes.POSITION].min, g.accessors[p.attributes.POSITION].max)
print('mats',[(i,m.name) for i,m in enumerate(g.materials)])
for a in g.animations:
    t=g.accessors[a.samplers[0].input]
    print(a.name,t.max,t.count)
