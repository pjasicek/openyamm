"""Texture pass: uv3d for compose_dagrell.py. The MM9 region transfer (spikes) must see the positions it always saw:
the rest pose of work/uv_v5.blend, in the MM9 mesh's space; repivot_dagrell.py moved the rest pose of uv_v6 away from it.
Each face of the new UV blend takes its uv_v5 corners through the old UVs (faces of uv_v5 and uv_v6 carry the same UVs;
left limbs share the right twin's texels, so they get the right twin's positions).

Args: <uv_v5.blend> <uv_v6.blend> <new uv blend> <out npz>
"""
import bpy, sys
from collections import defaultdict
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body'].data
    uv = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers['UVMap'].data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    lo = np.array([p.loop_start for p in me.polygons])
    f_uv = uv[(lo[:, None] + np.arange(3)).ravel()].reshape(-1, 3, 2)
    pos = np.array([v.co for v in me.vertices], np.float32)
    tri = np.array([p.vertices[:] for p in me.polygons])
    return f_uv, pos[tri], tri


uv5, xyz5, _ = load(argv[0])
uv6, xyz6, tri6 = load(argv[1])
uv7, xyz7, tri7 = load(argv[2])
assert np.array_equal(tri6, tri7) and np.abs(xyz6 - xyz7).max() < 1e-6
table = defaultdict(list)
for f in range(len(uv5)):
    table[tuple(sorted(map(tuple, np.round(uv5[f], 5))))].append(f)
xyz = np.zeros_like(xyz7)
missing = 0
for f in range(len(uv6)):
    hit = table.get(tuple(sorted(map(tuple, np.round(uv6[f], 5)))))
    if not hit:
        missing += 1
        xyz[f] = xyz6[f]
        continue
    g = max(hit, key=lambda i: xyz5[i, :, 0].mean())          # the right twin
    for k in range(3):
        xyz[f, k] = xyz5[g, int(np.argmin(np.abs(uv5[g] - uv6[f, k]).sum(1)))]
print('UV3D faces', len(uv6), 'missing in v5', missing)
np.savez(argv[3], uv=uv7, xyz=xyz)
