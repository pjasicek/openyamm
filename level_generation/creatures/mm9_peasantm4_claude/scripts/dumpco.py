import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects[argv[2]] if len(argv) > 2 else next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([o.matrix_world @ v.co for v in o.data.vertices], np.float32)
tris = []
for p in o.data.polygons:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1): tris.append([vs[0], vs[k], vs[k + 1]])
vg = {g.index: g.name for g in o.vertex_groups}
dom = []
for v in o.data.vertices:
    g = max(v.groups, key=lambda g: g.weight) if len(v.groups) else None
    dom.append(vg[g.group] if g else '')
np.savez(argv[1], co=co, tris=np.array(tris, np.int32), dom=np.array(dom))
print('DUMP', o.name, len(co))
