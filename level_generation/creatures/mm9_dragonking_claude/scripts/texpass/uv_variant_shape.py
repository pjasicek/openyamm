"""Layout shape of a variant blend: islands, fragment surface, stretch and use per set, without a GLB.
Args (Blender): <blend> <label> [report jsonl]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
n = len(me.polygons)
hd, mo = np.zeros(n, np.int32), np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd); me.attributes['mouth'].data.foreach_get('value', mo)
pos = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', pos); pos = pos.reshape(-1, 3)
lv = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv); tri = lv.reshape(-1, 3)


def measure(layer, sel, size=2048):
    f = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers[layer].data.foreach_get('uv', f); uv = f.reshape(-1, 3, 2)[sel]
    t = tri[sel]; p = pos[t]
    A3 = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    A2 = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    # islands: union by (vertex, uv)
    keys = {}; parent = list(range(len(t)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(len(t)):
        for k in range(3):
            key = (int(t[i, k]), round(float(uv[i, k, 0]), 6), round(float(uv[i, k, 1]), 6))
            j = keys.setdefault(key, i)
            parent[find(i)] = find(j)
    roots = np.array([find(i) for i in range(len(t))]); ids, inv, cnt = np.unique(roots, return_inverse=True, return_counts=True)
    frag = float(A3[cnt[inv] < 8].sum() / A3.sum())
    dens = np.sqrt(A2 / np.maximum(A3, 1e-12)) * size
    o = np.argsort(dens); w = np.cumsum(A3[o]) / A3.sum()
    pc = lambda q: float(dens[o][np.searchsorted(w, q)])
    return {'use': round(float(A2.sum()), 4), 'islands': len(ids), 'fragments': round(frag, 4), 'texels_per_unit': round(pc(.5), 1),
            'spread': round(pc(.9) / pc(.1), 3), 'zero': int((A2 < 1e-10).sum())}


r = {'label': a[1], 'body': measure('UVMap', hd == 0), 'head': measure('HeadUV', (hd > 0) & (mo == 0))}
print('SHAPE', json.dumps(r))
